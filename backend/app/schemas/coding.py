from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


MAX_CODE_CHARS = 20_000


class ProblemListItem(BaseModel):
    id: int
    title: str
    difficulty: str
    topic_id: int
    topic: str
    language: str


class ProblemOut(ProblemListItem):
    description: str
    examples: list
    tags: list[str]
    hints: list[str]
    constraints: str
    starter_code: str
    entry_function: str
    expected_complexity: str | None = None
    visible_tests: int
    hidden_tests: int


class CodeIn(BaseModel):
    problem_id: int
    code: str = Field(
        min_length=1,
        max_length=MAX_CODE_CHARS,
    )
    language: str = "python"


class TestResultOut(BaseModel):
    test_id: int
    index: int
    hidden: bool
    passed: bool
    input: list | None = None
    expected: Any = None
    actual: str | None = None
    error: str | None = None
    timed_out: bool = False
    time_ms: float = 0.0
    stdout: str | None = None


class RunOut(BaseModel):
    status: str
    passed: int
    total: int
    error: str | None = None
    results: list[TestResultOut]


class SubmitOut(RunOut):
    submission_id: int
    execution_time_ms: float


class SubmissionOut(BaseModel):
    id: int
    problem_id: int
    status: str
    passed: int
    total: int
    execution_time: float
    code: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ProgressRecentSubmission(BaseModel):
    problem_id: int
    status: str
    passed: int
    total: int
    language: str
    created_at: datetime


class ProgressOut(BaseModel):
    total_submissions: int
    problems_attempted: int
    problems_solved: int
    tests_passed: int
    tests_total: int
    test_accuracy: float
    python_submissions: int
    javascript_submissions: int
    recent_submissions: list[ProgressRecentSubmission]