import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import AskRequest, AskResponse, SourceChunk
from app.services.embedding_service import query_collection
from app.services.llm_service import ask_question

logger = logging.getLogger("study_companion")

router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Step 1: Retrieve relevant chunks from ChromaDB
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

        # Step 2: Send to Gemini with context
        answer = ask_question(request.question, chunks)

        # Step 3: Format sources for citation
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
