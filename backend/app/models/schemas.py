from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_stored: int
    collection_name: str


class AskRequest(BaseModel):
    question: str
    collection_name: str
    subject_id: int
    top_k: Optional[int] = 3


class SourceChunk(BaseModel):
    text: str
    source: str
    page: Optional[int] = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class QuizRequest(BaseModel):
    collection_name: str
    num_questions: Optional[int] = 5
    topic: Optional[str] = None


class MCQOption(BaseModel):
    label: str
    text: str


class MCQQuestion(BaseModel):
    question: str
    options: list[MCQOption]
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    questions: list[MCQQuestion]
    collection_name: str

# --- Subject schemas ---
class SubjectCreate(BaseModel):
    name: str

class SubjectResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    file_count: int = 0

    class Config:
        from_attributes = True

# --- File schemas ---
class FileResponse(BaseModel):
    id: int
    subject_id: int
    filename: str
    collection_name: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# --- Quiz session schemas ---
class QuizSessionCreate(BaseModel):
    subject_id: int
    file_id: int
    score: int
    total: int
    results: list[dict]

class QuizSessionResponse(BaseModel):
    id: int
    subject_id: int
    file_id: int
    score: int
    total: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Dashboard schemas ---
class WeakTopic(BaseModel):
    topic: str
    wrong_count: int

class SubjectStats(BaseModel):
    subject_id: int
    subject_name: str
    total_quizzes: int
    average_score: float
    weak_topics: list[WeakTopic]

class DashboardResponse(BaseModel):
    subjects: list[SubjectStats]