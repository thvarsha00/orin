"""Orin Code API.

Browse coding problems, run visible tests, and submit against
visible + hidden tests.
"""

import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import (
    CodingProblem,
    Submission,
    SubmissionResult,
    TestCase,
    Topic,
    User,
)
from app.schemas.coding import (
    CodeIn,
    ProblemListItem,
    ProblemOut,
    ProgressOut,
    ProgressRecentSubmission,
    RunOut,
    SubmissionOut,
    SubmitOut,
    TestResultOut,
)
from app.services.coding.evaluator import (
    Evaluation,
    TestSpec,
    evaluate,
)
from app.services.coding.executor import (
    RunnerUnavailable,
    run_code,
)


router = APIRouter(
    prefix="/api/coding",
    tags=["coding"],
)


_slots = threading.BoundedSemaphore(
    max(1, settings.code_max_concurrent)
)

BUSY_WAIT_SECONDS = 10


SUPPORTED_LANGUAGES = {
    "python",
    "javascript",
    "java",
}


def _can_see(user: User):
    return or_(
        CodingProblem.status == "published",
        CodingProblem.owner_id == user.id,
    )


def _problem_for(
    db: Session,
    user: User,
    problem_id: int,
) -> CodingProblem:

    problem = db.scalar(
        select(CodingProblem).where(
            CodingProblem.id == problem_id,
            _can_see(user),
        )
    )

    if not problem:
        raise HTTPException(
            404,
            "Problem not found.",
        )

    return problem


def _tests_for(
    db: Session,
    problem_id: int,
    *,
    include_hidden: bool,
) -> list[TestCase]:

    q = (
        select(TestCase)
        .where(TestCase.problem_id == problem_id)
        .order_by(TestCase.id)
    )

    if not include_hidden:
        q = q.where(
            TestCase.is_hidden.is_(False)
        )

    return list(db.scalars(q))


def _execute(
    problem: CodingProblem,
    tests: list[TestCase],
    code: str,
    language: str,
) -> Evaluation:

    # Local subprocess execution is intentionally blocked unless
    # explicitly enabled for trusted private development.
    #
    # Docker remains the recommended production sandbox.
    if (
        settings.code_runner.lower() == "subprocess"
        and not settings.code_allow_unsafe_local
    ):
        raise HTTPException(
            503,
            (
                "Local code execution is disabled. "
                "Enable CODE_ALLOW_UNSAFE_LOCAL=1 only for trusted "
                "development on a private machine."
            ),
        )

    language = language.strip().lower()

    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            422,
            f"Language '{language}' is not supported yet.",
        )

    # A problem belongs to one language.
    # This prevents Python code from being submitted to a
    # JavaScript/Java problem and vice versa.
    if problem.language.lower() != language:
        raise HTTPException(
            422,
            (
                f"This problem is a "
                f"{problem.language} problem. "
                f"Submit code using {problem.language}."
            ),
        )

    if not tests:
        raise HTTPException(
            409,
            "This problem has no test cases yet.",
        )

    specs = [
        TestSpec(
            t.id,
            t.input_data,
            t.expected_output,
            t.is_hidden,
        )
        for t in tests
    ]

    if not _slots.acquire(
        timeout=BUSY_WAIT_SECONDS
    ):
        raise HTTPException(
            503,
            (
                "The code runner is busy right now. "
                "Please try again in a moment."
            ),
        )

    try:

        report = run_code(
            language=language,
            code=code,
            entry=problem.entry_function,
            inputs=[
                s.input_data
                for s in specs
            ],
            runner=settings.code_runner.lower(),
            per_case_seconds=settings.code_time_limit_seconds,
            docker_image=settings.code_docker_image,
            memory_mb=settings.code_memory_mb,
        )

    except RunnerUnavailable as exc:

        raise HTTPException(
            503,
            str(exc),
        )

    finally:
        _slots.release()

    return evaluate(
        specs,
        report,
    )


def _results_out(
    tests: list[TestCase],
    ev: Evaluation,
) -> list[TestResultOut]:

    out = []

    for index, (
        test,
        verdict,
    ) in enumerate(
        zip(tests, ev.verdicts),
        start=1,
    ):

        if test.is_hidden:

            reason = (
                "Time limit exceeded"
                if verdict.timed_out
                else
                "Runtime error"
                if verdict.error
                else
                None
                if verdict.passed
                else
                "Wrong answer"
            )

            out.append(
                TestResultOut(
                    test_id=test.id,
                    index=index,
                    hidden=True,
                    passed=verdict.passed,
                    error=reason,
                    timed_out=verdict.timed_out,
                    time_ms=round(
                        verdict.time_ms,
                        2,
                    ),
                )
            )

        else:

            out.append(
                TestResultOut(
                    test_id=test.id,
                    index=index,
                    hidden=False,
                    passed=verdict.passed,
                    input=test.input_data,
                    expected=test.expected_output,
                    actual=verdict.actual,
                    error=verdict.error,
                    timed_out=verdict.timed_out,
                    time_ms=round(
                        verdict.time_ms,
                        2,
                    ),
                    stdout=(
                        verdict.stdout
                        or None
                    ),
                )
            )

    return out


@router.get(
    "/problems",
    response_model=list[ProblemListItem],
)
def list_problems(
    difficulty: str | None = None,
    topic_id: int | None = None,
    language: str | None = None,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    q = (
        select(
            CodingProblem,
            Topic.name,
        )
        .join(
            Topic,
            Topic.id == CodingProblem.topic_id,
        )
        .where(_can_see(user))
        .order_by(CodingProblem.id)
    )

    if difficulty:
        q = q.where(
            CodingProblem.difficulty
            == difficulty
        )

    if topic_id:
        q = q.where(
            CodingProblem.topic_id
            == topic_id
        )

    if language:
        language = language.strip().lower()

        if language not in {
            "python",
            "javascript",
        }:
            raise HTTPException(
                422,
                f"Language '{language}' is not supported yet.",
            )

        q = q.where(
            CodingProblem.language == language
        )

    return [
        ProblemListItem(
            id=problem.id,
            title=problem.title,
            difficulty=problem.difficulty,
            topic_id=problem.topic_id,
            topic=name,
            language=problem.language,
        )
        for problem, name in db.execute(q)
    ]


@router.get(
    "/problems/{problem_id}",
    response_model=ProblemOut,
)
def get_problem(
    problem_id: int,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    problem = _problem_for(
        db,
        user,
        problem_id,
    )

    tests = _tests_for(
        db,
        problem.id,
        include_hidden=True,
    )

    topic = db.get(
        Topic,
        problem.topic_id,
    )

    return ProblemOut(
        id=problem.id,
        title=problem.title,
        difficulty=problem.difficulty,
        topic_id=problem.topic_id,
        topic=topic.name,
        language=problem.language,
        description=problem.description,
        examples=problem.examples or [],
        tags=problem.tags or [],
        hints=problem.hints or [],
        constraints=problem.constraints,
        starter_code=problem.starter_code,
        entry_function=problem.entry_function,
        expected_complexity=problem.expected_complexity,
        visible_tests=sum(
            not t.is_hidden
            for t in tests
        ),
        hidden_tests=sum(
            t.is_hidden
            for t in tests
        ),
    )


@router.post(
    "/run",
    response_model=RunOut,
)
def run(
    data: CodeIn,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    """Run the submitted code against visible tests only."""

    problem = _problem_for(
        db,
        user,
        data.problem_id,
    )

    tests = _tests_for(
        db,
        problem.id,
        include_hidden=False,
    )

    ev = _execute(
        problem,
        tests,
        data.code,
        data.language,
    )

    return RunOut(
        status=ev.status,
        passed=ev.passed,
        total=ev.total,
        error=ev.error,
        results=_results_out(
            tests,
            ev,
        ),
    )


@router.post(
    "/submit",
    response_model=SubmitOut,
)
def submit(
    data: CodeIn,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    """Run against visible + hidden tests and save the attempt."""

    problem = _problem_for(
        db,
        user,
        data.problem_id,
    )

    tests = _tests_for(
        db,
        problem.id,
        include_hidden=True,
    )

    ev = _execute(
        problem,
        tests,
        data.code,
        data.language,
    )

    submission = Submission(
        user_id=user.id,
        problem_id=problem.id,
        code=data.code,
        language=data.language,
        status=ev.status,
        passed=ev.passed,
        total=ev.total,
        execution_time=round(
            ev.total_time_s,
            4,
        ),
        hints_used=0,
    )

    submission.results = [
        SubmissionResult(
            test_case_id=test.id,
            passed=verdict.passed,
            actual_output=verdict.actual,
            stderr=verdict.error,
            execution_time=round(
                verdict.time_ms / 1000,
                4,
            ),
        )
        for test, verdict
        in zip(
            tests,
            ev.verdicts,
        )
    ]

    db.add(submission)
    db.commit()

    return SubmitOut(
        submission_id=submission.id,
        status=ev.status,
        passed=ev.passed,
        total=ev.total,
        error=ev.error,
        execution_time_ms=round(
            ev.total_time_s * 1000,
            2,
        ),
        results=_results_out(
            tests,
            ev,
        ),
    )


@router.get(
    "/problems/{problem_id}/submissions",
    response_model=list[SubmissionOut],
)
def my_submissions(
    problem_id: int,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    _problem_for(
        db,
        user,
        problem_id,
    )

    q = (
        select(Submission)
        .where(
            Submission.user_id == user.id,
            Submission.problem_id == problem_id,
        )
        .order_by(
            Submission.id.desc()
        )
        .limit(20)
    )

    return list(
        db.scalars(q)
    )


@router.get(
    "/progress",
    response_model=ProgressOut,
)
def coding_progress(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """Return real coding progress from the user's submissions."""

    submissions = list(
        db.scalars(
            select(Submission)
            .where(
                Submission.user_id == user.id
            )
            .order_by(
                Submission.id.desc()
            )
        )
    )

    total_submissions = len(
        submissions
    )

    problems_attempted = len(
        {
            submission.problem_id
            for submission in submissions
        }
    )

    solved_problem_ids = {
        submission.problem_id
        for submission in submissions
        if submission.status == "passed"
    }

    problems_solved = len(
        solved_problem_ids
    )

    tests_passed = sum(
        submission.passed
        for submission in submissions
    )

    tests_total = sum(
        submission.total
        for submission in submissions
    )

    test_accuracy = (
        round(
            (
                tests_passed
                / tests_total
            )
            * 100,
            2,
        )
        if tests_total
        else 0.0
    )

    python_submissions = sum(
        1
        for submission in submissions
        if submission.language.lower()
        == "python"
    )

    javascript_submissions = sum(
        1
        for submission in submissions
        if submission.language.lower()
        == "javascript"
    )

    recent_submissions = [
        ProgressRecentSubmission(
            problem_id=submission.problem_id,
            status=submission.status,
            passed=submission.passed,
            total=submission.total,
            language=submission.language,
            created_at=submission.created_at,
        )
        for submission in submissions[:10]
    ]

    return ProgressOut(
        total_submissions=total_submissions,
        problems_attempted=problems_attempted,
        problems_solved=problems_solved,
        tests_passed=tests_passed,
        tests_total=tests_total,
        test_accuracy=test_accuracy,
        python_submissions=python_submissions,
        javascript_submissions=javascript_submissions,
        recent_submissions=recent_submissions,
    )