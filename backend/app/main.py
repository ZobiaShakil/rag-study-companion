from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes_upload import router as upload_router
from app.core.logging_config import setup_logging
from app.config import get_settings

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting Study Companion backend...")
    logger.info(f"Chroma persist dir: {settings.chroma_persist_dir}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    yield
    logger.info("Shutting down Study Companion backend...")


app = FastAPI(
    title="AI Study Companion",
    description="RAG-based study assistant for course material",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)

@app.get("/health")
def health():
    return {"status": "ok", "message": "Study Companion backend is running"}

@app.get("/")
def root():
    return {"message": "Welcome to the AI Study Companion backend!"}    