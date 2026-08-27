import logging
import json
import re
from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select
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
        question_text = r.get("question", "")
        topic = r.get("topic", None)
        is_correct = r.get("is_correct", False)

        # If the user got this question correct, remove prior wrong results
        # for the same subject/topic so the topic no longer counts as a weak topic.
        if is_correct and topic:
            try:
                subq = select(QuizSession.id).where(QuizSession.subject_id == data.subject_id).scalar_subquery()
                await db.execute(
                    delete(QuizResult).where(
                        QuizResult.session_id.in_(subq),
                        QuizResult.topic == topic,
                        QuizResult.is_correct == False
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to cleanup previous wrong results: {e}")

        result = QuizResult(
            session_id=session.id,
            question=question_text,
            correct_answer=r.get("correct_answer", ""),
            user_answer=r.get("user_answer", ""),
            is_correct=is_correct,
            topic=topic
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


        questions_data = json.loads(cleaned)
        logger.error(f"TYPE: {type(questions_data)}")
        logger.error(f"CONTENT: {questions_data}")

        # If the model returned a JSON string, decode it.
        if isinstance(questions_data, str):
            questions_data = json.loads(questions_data)

        # If the model returned an object (e.g. numbered dict), convert to list of values.
        if isinstance(questions_data, dict):
            questions_data = list(questions_data.values())

        # If the list contains JSON-encoded strings for each question, decode them.
        if isinstance(questions_data, list):
            normalized = []
            for item in questions_data:
                if isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                    except json.JSONDecodeError:
                        parsed = item
                    normalized.append(parsed)
                else:
                    normalized.append(item)
            questions_data = normalized

        if not isinstance(questions_data, list):
            raise HTTPException(
                status_code=500,
                detail="Quiz generation failed — unexpected response structure from model."
            )

        questions = []
        for idx, q in enumerate(questions_data, start=1):
            # Ensure each item is a dict
            if isinstance(q, str):
                try:
                    q = json.loads(q)
                except json.JSONDecodeError:
                    logger.error(f"Question #{idx} is a plain string and not JSON: {q}")
                    raise HTTPException(status_code=500, detail="Quiz generation failed — invalid question format.")

            if not isinstance(q, dict):
                logger.error(f"Question #{idx} has unexpected type: {type(q)}")
                raise HTTPException(status_code=500, detail="Quiz generation failed — unexpected question format.")

            raw_options = q.get("options")
            if raw_options is None:
                logger.error(f"Question #{idx} missing 'options' field: {q}")
                raise HTTPException(status_code=500, detail="Quiz generation failed — question missing options.")

            parsed_options = []

            # If options is a dict mapping labels -> text
            if isinstance(raw_options, dict):
                for label, text in raw_options.items():
                    parsed_options.append(MCQOption(label=str(label).strip(), text=str(text).strip()))

            # If options is a list, handle dict items or strings
            elif isinstance(raw_options, list):
                for i, opt in enumerate(raw_options):
                    if isinstance(opt, dict) and "label" in opt and "text" in opt:
                        parsed_options.append(MCQOption(label=str(opt["label"]).strip(), text=str(opt["text"]).strip()))
                    elif isinstance(opt, str):
                        # Try to extract an explicit label like 'A) text' or 'A. text' or 'A: text'
                        m = re.match(r"^\s*([A-Za-z])\s*[\)\.:\-]\s*(.*)$", opt)
                        if m:
                            label = m.group(1).upper()
                            text = m.group(2).strip()
                        else:
                            label = chr(ord("A") + i)
                            text = opt.strip()
                        parsed_options.append(MCQOption(label=label, text=text))
                    else:
                        logger.error(f"Question #{idx} has an option with unexpected type: {type(opt)}")
                        raise HTTPException(status_code=500, detail="Quiz generation failed — invalid option format.")

            else:
                logger.error(f"Question #{idx} options field has unexpected type: {type(raw_options)}")
                raise HTTPException(status_code=500, detail="Quiz generation failed — invalid options structure.")

            # Normalize correct answer: if it's full text, map to the corresponding label
            correct = q.get("correct_answer")
            if correct is None:
                logger.error(f"Question #{idx} missing 'correct_answer': {q}")
                raise HTTPException(status_code=500, detail="Quiz generation failed — missing correct answer.")

            correct_label = None
            if isinstance(correct, str) and len(correct.strip()) == 1 and correct.strip().isalpha():
                correct_label = correct.strip().upper()
            else:
                # try to match by option text
                for opt in parsed_options:
                    if str(opt.text).strip().lower() == str(correct).strip().lower():
                        correct_label = opt.label
                        break

            if correct_label is None:
                # As a fallback, if correct is like 'A) ...' extract letter
                if isinstance(correct, str):
                    m = re.match(r"^\s*([A-Za-z])\b", correct)
                    if m:
                        correct_label = m.group(1).upper()

            if correct_label is None:
                logger.error(f"Unable to determine correct option label for question #{idx}: {correct} -> options {parsed_options}")
                raise HTTPException(status_code=500, detail="Quiz generation failed — cannot determine correct answer mapping.")

            questions.append(MCQQuestion(
                question=str(q.get("question", "")).strip(),
                options=parsed_options,
                correct_answer=correct_label,
                explanation=str(q.get("explanation", "")).strip(),
                topic=q.get("topic", "General")
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