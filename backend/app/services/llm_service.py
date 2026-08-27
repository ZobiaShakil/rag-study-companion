import logging
from types import SimpleNamespace
from typing import List, Dict, Any

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - allows tests to run without the SDK installed
    genai = None

try:
    from app.config import get_settings
except ImportError:  # pragma: no cover - allows tests to run without settings dependencies
    def get_settings():
        return SimpleNamespace(gemini_api_key="")

logger = logging.getLogger("study_companion")

_model = None


def get_gemini_model():
    global _model
    if _model is None:
        if genai is None:
            raise RuntimeError("google-generativeai is not installed")
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Gemini model initialized")
    return _model


def build_chat_history_for_model(chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a sanitized history that preserves user turns but drops prior model answers."""
    sanitized_history = []

    for msg in chat_history or []:
        role = msg.get("role")
        parts = msg.get("parts", [""])
        content = parts[0] if parts else ""

        if role != "user" or not content or not str(content).strip():
            continue

        content = str(content).strip()
        if "[Source" in content:
            content = content.split("[Source")[0].strip()

        sanitized_history.append({"role": "user", "parts": [content]})

    return sanitized_history


def generate_chat_response(
    question: str, 
    context_chunks: List[Dict[str, Any]], 
    chat_history: List[Dict[str, Any]]
) -> str:
    """
    Handles multi-turn Q&A using Gemini's native chat tracking, with dynamic
    history sanitization to enforce layout constraints.
    """
    # 1. Format the RAG context from ChromaDB
    context = ""
    for i, chunk in enumerate(context_chunks, start=1):
        context += f"\n[Source {i}: {chunk['source']}, Slide {chunk['page']}]\n{chunk['text']}\n"

    # 2. Set strict system and grounding constraints
    system_instruction = f"""You are a helpful, precise university study assistant. 
Answer the student's question using ONLY the course context provided below.
If the answer cannot be found or reasonably inferred from the context, state: "I couldn't find this in your uploaded notes."

CRITICAL HISTORY RULE: Answer ONLY the user's latest question directly. Do NOT repeat, summarize, or blend answers from previous conversation turns.
CRITICAL FORMATTING RULE: Do NOT include any inline citations, bracketed sources, or text references (e.g., do NOT write "[Source 1]" or "(Slide 14)" anywhere inside your response sentences).
RULE: Answer these types of questions too for eg: "explain the first 2 slides content"
COURSE CONTEXT:
{context}"""

    # 3. Do not forward prior chat history to Gemini for now.
    # Prior user turns without assistant replies can cause the model to blend
    # previous answers into the current response.
    clean_history = []

    # 4. Initialize the dynamic generative workspace context instance
    if genai is None:
        raise RuntimeError("google-generativeai is not installed")

    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)

    logger.info(f"Starting chat turn for question: {question[:50]}...")

    # 5. Spin up the chat session using sanitized memory nodes
    chat = model.start_chat(history=clean_history)

    # 6. Execute inference response string generation
    response = chat.send_message(question)
    logger.info("Received conversational response from Gemini")

    return response.text


def build_quiz_prompt(context_chunks: List[Dict[str, Any]], num_questions: int, topic: str = None) -> str:
    context = ""
    for chunk in context_chunks:
        context += f"\n[{chunk['source']}, Slide {chunk['page']}]\n{chunk['text']}\n"

    topic_line = f"Focus on the topic: {topic}" if topic else "Cover the key concepts from the material."

    return f"""You are a university professor creating an exam.
Generate exactly {num_questions} multiple choice questions from the study material below.
{topic_line}

For each question, include a short "topic" field (2-4 words) naming the specific concept it tests, e.g. "MPI vs OpenMP" or "Scheduling vs Mapping".

Return ONLY a JSON array, no explanation, no markdown, no backticks. Example format:
[
  {{
    "question": "What is X?",
    "options": [...],
    "correct_answer": "A",
    "explanation": "Because X is...",
    "topic": "Short topic name"
  }}
]

STUDY MATERIAL:
{context}"""


def generate_quiz(
    context_chunks: List[Dict[str, Any]],
    num_questions: int = 5,
    topic: str = None
) -> str:
    model = get_gemini_model()
    prompt = build_quiz_prompt(context_chunks, num_questions, topic)

    logger.info(f"Generating {num_questions} quiz questions...")
    response = model.generate_content(prompt)
    logger.info("Quiz generated")

    return response.text