from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_stored: int
    collection_name: str


class AskRequest(BaseModel):
    question: str
    collection_name: str
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