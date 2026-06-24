import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from app.config import get_settings
from app.services.doc_processor import TextChunk

logger = logging.getLogger("study_companion")

_embedding_model = None
_chroma_client = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _embedding_model


def get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB client initialized at {settings.chroma_persist_dir}")
    return _chroma_client


def store_chunks(
    chunks: list[TextChunk],
    collection_name: str
) -> int:
    model = get_embedding_model()
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    ids = [f"{collection_name}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": chunk.source, "page": chunk.page}
        for chunk in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    logger.info(f"Stored {len(chunks)} chunks in collection '{collection_name}'")
    return len(chunks)


def query_collection(
    question: str,
    collection_name: str,
    top_k: int = 3
) -> list[dict]:
    model = get_embedding_model()
    client = get_chroma_client()

    collection = client.get_collection(name=collection_name)
    question_embedding = model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "page": results["metadatas"][0][i]["page"],
            "distance": results["distances"][0][i]
        })

    logger.info(f"Retrieved {len(chunks)} chunks for query from '{collection_name}'")
    return chunks