import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.models.database import get_db, Subject, SubjectFile, QuizSession, QuizResult
from app.models.schemas import SubjectCreate, SubjectResponse, FileResponse, DashboardResponse, SubjectStats, WeakTopic
from app.services.embedding_service import get_chroma_client

logger = logging.getLogger("study_companion")
router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("/", response_model=SubjectResponse)
async def create_subject(data: SubjectCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Subject).where(Subject.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject with this name already exists.")

    subject = Subject(name=data.name)
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    logger.info(f"Created subject: {data.name}")

    return SubjectResponse(
        id=subject.id,
        name=subject.name,
        created_at=subject.created_at,
        file_count=0
    )


@router.get("/", response_model=list[SubjectResponse])
async def get_subjects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject))
    subjects = result.scalars().all()

    response = []
    for subject in subjects:
        count_result = await db.execute(
            select(func.count(SubjectFile.id)).where(SubjectFile.subject_id == subject.id)
        )
        file_count = count_result.scalar() or 0
        response.append(SubjectResponse(
            id=subject.id,
            name=subject.name,
            created_at=subject.created_at,
            file_count=file_count
        ))
    return response


@router.get("/{subject_id}/files", response_model=list[FileResponse])
async def get_subject_files(subject_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SubjectFile).where(SubjectFile.subject_id == subject_id)
    )
    return result.scalars().all()


@router.delete("/{subject_id}")
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    # Get subject
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    # Get all files before deleting so we have collection names
    files_result = await db.execute(
        select(SubjectFile).where(SubjectFile.subject_id == subject_id)
    )
    files = files_result.scalars().all()

    # Delete ChromaDB collections for each file
    chroma = get_chroma_client()
    for file in files:
        try:
            chroma.delete_collection(file.collection_name)
            logger.info(f"Deleted ChromaDB collection: {file.collection_name}")
        except Exception as e:
            logger.warning(f"Could not delete collection {file.collection_name}: {e}")

    # Delete subject from SQLite (cascade handles files, sessions, results)
    await db.delete(subject)
    await db.commit()
    return {"message": "Subject deleted"}


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    subjects_result = await db.execute(select(Subject))
    subjects = subjects_result.scalars().all()

    stats = []
    for subject in subjects:
        sessions_result = await db.execute(
            select(QuizSession).where(QuizSession.subject_id == subject.id)
        )
        sessions = sessions_result.scalars().all()

        if not sessions:
            stats.append(SubjectStats(
                subject_id=subject.id,
                subject_name=subject.name,
                total_quizzes=0,
                average_score=0.0,
                weak_topics=[]
            ))
            continue

        total_quizzes = len(sessions)
        avg_score = sum(
            (s.score / s.total * 100) if s.total > 0 else 0
            for s in sessions
        ) / total_quizzes

        # Find weak topics from wrong answers
        session_ids = [s.id for s in sessions]
        wrong_results = await db.execute(
            select(QuizResult).where(
                QuizResult.session_id.in_(session_ids),
                QuizResult.is_correct == False
            )
        )
        wrong = wrong_results.scalars().all()

        topic_counts: dict[str, int] = {}
        for r in wrong:
            if r.topic:
                topic_counts[r.topic] = topic_counts.get(r.topic, 0) + 1

        # Return only the topic names, sorted by descending wrong_count, top 5
        weak_topics = [
            WeakTopic(topic=t)
            for t, c in sorted(topic_counts.items(), key=lambda x: -x[1])
        ][:5]

        stats.append(SubjectStats(
            subject_id=subject.id,
            subject_name=subject.name,
            total_quizzes=total_quizzes,
            average_score=round(avg_score, 1),
            weak_topics=weak_topics
        ))

    return DashboardResponse(subjects=stats)