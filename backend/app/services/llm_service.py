import logging
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger("study_companion")

_model = None


def get_gemini_model():
    global _model
    if _model is None:
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Gemini model initialized")
    return _model


def build_qa_prompt(question: str, context_chunks: list[dict]) -> str:
    context = ""
    for i, chunk in enumerate(context_chunks, start=1):
        context += f"\n[Source {i}: {chunk['source']}, Slide {chunk['page']}]\n{chunk['text']}\n"

    return f"""You are a study assistant. Answer the student's question using ONLY the context provided below.
If the answer is not in the context, say "I couldn't find this in your uploaded notes."
Always mention which source and slide number your answer came from.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""


def ask_question(question: str, context_chunks: list[dict]) -> str:
    model = get_gemini_model()
    prompt = build_qa_prompt(question, context_chunks)

    logger.info(f"Sending question to Gemini: {question[:50]}...")
    response = model.generate_content(prompt)
    logger.info("Received response from Gemini")

    return response.text


def build_quiz_prompt(context_chunks: list[dict], num_questions: int, topic: str = None) -> str:
    context = ""
    for chunk in context_chunks:
        context += f"\n[{chunk['source']}, Slide {chunk['page']}]\n{chunk['text']}\n"

    topic_line = f"Focus on the topic: {topic}" if topic else "Cover the key concepts from the material."

    return f"""You are a university professor creating an exam.
Generate exactly {num_questions} multiple choice questions from the study material below.
{topic_line}

Return ONLY a JSON array, no explanation, no markdown, no backticks. Example format:
[
  {{
    "question": "What is X?",
    "options": [
      {{"label": "A", "text": "First option"}},
      {{"label": "B", "text": "Second option"}},
      {{"label": "C", "text": "Third option"}},
      {{"label": "D", "text": "Fourth option"}}
    ],
    "correct_answer": "A",
    "explanation": "Because X is..."
  }}
]

STUDY MATERIAL:
{context}"""


def generate_quiz(
    context_chunks: list[dict],
    num_questions: int = 5,
    topic: str = None
) -> str:
    model = get_gemini_model()
    prompt = build_quiz_prompt(context_chunks, num_questions, topic)

    logger.info(f"Generating {num_questions} quiz questions...")
    response = model.generate_content(prompt)
    logger.info("Quiz generated")

    return response.text