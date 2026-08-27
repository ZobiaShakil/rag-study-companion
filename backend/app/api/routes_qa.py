import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.database import get_db, ChatMessage 
from app.models.schemas import AskRequest, AskResponse, SourceChunk, ChatMessageResponse
from app.services.embedding_service import query_collection
from app.services.llm_service import generate_chat_response

logger = logging.getLogger("study_companion")

router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, db: AsyncSession = Depends(get_db)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Step 1: Retrieve relevant chunks from ChromaDB for RAG context
        chunks = query_collection(
            question=request.question,
            collection_name=request.collection_name,
            top_k=request.top_k
        )

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"No content found in collection '{request.collection_name}'. Did you upload a file?"
            )

        # Step 3: Send to conversational Gemini service without prior chat history.
        answer = generate_chat_response(
            question=request.question,
            context_chunks=chunks,
            chat_history=[]
        )

        # Step 4: Save the current QA exchange back to history logs
        user_msg = ChatMessage(subject_id=request.subject_id, role="user", content=request.question)
        model_msg = ChatMessage(subject_id=request.subject_id, role="model", content=answer)
        
        db.add(user_msg)
        db.add(model_msg)
        await db.commit()

        # Step 5: Format source chunks for frontend citation panels
        sources = [
            SourceChunk(
                text=chunk["text"],
                source=chunk["source"],
                page=chunk["page"]
            )
            for chunk in chunks
        ]

        return AskResponse(answer=answer, sources=sources)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")


@router.get('/history/{subject_id}', response_model=list[ChatMessageResponse])
async def get_history(subject_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.subject_id == subject_id).order_by(ChatMessage.timestamp)
        )
        messages = result.scalars().all()

        return [ChatMessageResponse(role=m.role, content=m.content, timestamp=m.timestamp) for m in messages]
    except Exception as e:
        logger.error(f"Failed to fetch chat history for subject {subject_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve chat history")