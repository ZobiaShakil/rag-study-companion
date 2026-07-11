import logging
import json
from fastapi import APIRouter, HTTPException
from app.models.schemas import QuizRequest, QuizResponse, MCQQuestion, MCQOption, QuizSessionCreate
from app.services.embedding_service import query_collection
from app.services.llm_service import generate_quiz
from app.models.database import get_db, QuizSession, QuizResult
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

logger = logging.getLogger("study_companion")

router = APIRouter(prefix="/quiz", tags=["Quiz"])

@router.post("/sessions")
async def save_quiz_session(
    data: QuizSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    session = QuizSession(
        subject_id=data.subject_id,
        file_id=data.file_id,
        score=data.score,
        total=data.total
    )
    db.add(session)
    await db.flush()  # get session.id before committing

    for r in data.results:
        result = QuizResult(
            session_id=session.id,
            question=r.get("question", ""),
            correct_answer=r.get("correct_answer", ""),
            user_answer=r.get("user_answer", ""),
            is_correct=r.get("is_correct", False),
            topic=r.get("topic", None)
        )
        db.add(result)

    await db.commit()
    logger.info(f"Saved quiz session: score {data.score}/{data.total}")
    return {"message": "Session saved", "session_id": session.id}

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz_endpoint(request: QuizRequest):
    try:
        # Retrieve relevant chunks
        query = request.topic if request.topic else "key concepts definitions important topics"
        chunks = query_collection(
            question=query,
            collection_name=request.collection_name,
            top_k=10
        )

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"No content found in collection '{request.collection_name}'. Did you upload a file?"
            )

        # Generate quiz from Gemini
        raw_response = generate_quiz(
            context_chunks=chunks,
            num_questions=request.num_questions,
            topic=request.topic
        )

        # Parse JSON response
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        # temporary debug — remove after fixing
        logger.error(f"Raw Gemini response: {cleaned}")

        questions_data = json.loads(cleaned)

        # Convert to Pydantic models
        questions = []
        for q in questions_data:
            options = [
                MCQOption(label=opt["label"], text=opt["text"])
                for opt in q["options"]
            ]
            questions.append(MCQQuestion(
                question=q["question"],
                options=options,
                correct_answer=q["correct_answer"],
                explanation=q["explanation"]
            ))

        return QuizResponse(
            questions=questions,
            collection_name=request.collection_name
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini quiz response as JSON: {e}")
        raise HTTPException(
            status_code=500,
            detail="Quiz generation failed — model returned invalid format. Try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")