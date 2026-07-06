from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime
from app.config import get_settings

Base = declarative_base()


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    files = relationship("SubjectFile", back_populates="subject", cascade="all, delete")
    quiz_sessions = relationship("QuizSession", back_populates="subject", cascade="all, delete")


class SubjectFile(Base):
    __tablename__ = "subject_files"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    filename = Column(String, nullable=False)
    collection_name = Column(String, unique=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="files")
    quiz_sessions = relationship("QuizSession", back_populates="file", cascade="all, delete")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("subject_files.id"), nullable=False)
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="quiz_sessions")
    file = relationship("SubjectFile", back_populates="quiz_sessions")
    results = relationship("QuizResult", back_populates="session", cascade="all, delete")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("quiz_sessions.id"), nullable=False)
    question = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    topic = Column(String, nullable=True)

    session = relationship("QuizSession", back_populates="results")


def get_database_url() -> str:
    return "sqlite+aiosqlite:///./study_companion.db"


engine = create_async_engine(
    get_database_url(),
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)