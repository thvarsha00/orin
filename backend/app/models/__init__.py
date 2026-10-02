from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    skill_level: Mapped[str] = mapped_column(String(20), default="beginner")
    preferred_script: Mapped[str] = mapped_column(String(10), default="auto")  # auto | roman | native
    last_detected_script: Mapped[str | None] = mapped_column(String(10), nullable=True)
    user: Mapped[User] = relationship(back_populates="profile")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="New conversation")
    language: Mapped[str] = mapped_column(String(10), default="en")
    level: Mapped[str] = mapped_column(String(20), default="beginner")
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan",
                                                     order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)  # relative to UPLOAD_DIR
    image_mime: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    @property
    def has_image(self) -> bool:
        return bool(self.image_path)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))  # display name (sanitised original name)
    file_type: Mapped[str] = mapped_column(String(20))  # pdf | txt | md
    file_path: Mapped[str | None] = mapped_column(String(255), nullable=True)  # relative to UPLOAD_DIR, server-generated
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    embed_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|extracting|embedding|ready|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None for plain-text files
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)  # L2-normalised float32 vector
    document: Mapped[Document] = relationship(back_populates="chunks")


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    prerequisite_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)


class CodingProblem(Base):
    __tablename__ = "coding_problems"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    language: Mapped[str] = mapped_column(String(20), default="python")
    examples: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    hints: Mapped[list] = mapped_column(JSON, default=list)
    constraints: Mapped[str] = mapped_column(Text, default="")
    starter_code: Mapped[str] = mapped_column(Text, default="")
    entry_function: Mapped[str] = mapped_column(String(100), default="solve")
    expected_complexity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Generated problems stay private + draft until validated.
    status: Mapped[str] = mapped_column(String(20), default="published")  # draft|validated|published
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="problem", cascade="all, delete-orphan")


class TestCase(Base):
    __test__ = False  # not a pytest class
    __tablename__ = "test_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("coding_problems.id"), index=True)
    input_data: Mapped[list] = mapped_column(JSON)  # list of positional args
    expected_output: Mapped[object] = mapped_column(JSON)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    problem: Mapped[CodingProblem] = relationship(back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("coding_problems.id"), index=True)
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(20), default="python")
    status: Mapped[str] = mapped_column(String(20))  # passed|failed|error|timeout
    passed: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    execution_time: Mapped[float] = mapped_column(Float, default=0.0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    results: Mapped[list["SubmissionResult"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class SubmissionResult(Base):
    __tablename__ = "submission_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"))
    passed: Mapped[bool] = mapped_column(Boolean)
    actual_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time: Mapped[float] = mapped_column(Float, default=0.0)
    submission: Mapped[Submission] = relationship(back_populates="results")


class UserTopicProgress(Base):
    __tablename__ = "user_topic_progress"
    __table_args__ = (UniqueConstraint("user_id", "topic_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    solved: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    mastery: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    reason: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)  # submission ids + accuracy snapshot
    suggested_problem_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)


class DailyChallenge(Base):
    __tablename__ = "daily_challenges"
    __table_args__ = (UniqueConstraint("user_id", "challenge_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("coding_problems.id"))
    challenge_date: Mapped[date] = mapped_column(Date)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
