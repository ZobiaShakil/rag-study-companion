# RAG Study Companion

An AI-powered study assistant that lets students upload course materials, generate embeddings, and ask questions based on those notes. The project combines a FastAPI backend with a React + Vite frontend and uses ChromaDB for retrieval-augmented generation.

## Demo
[Watch the demo video]([https://github.com/ZobiaShakil/rag-study-companion/blob/main/rag-study-companion%20(1).mp4])

## Key Features

- Create subjects to organize course material
- Upload PDFs and PPTX files
- Extract text, chunk content, and store embeddings in ChromaDB
- Retrieve relevant document chunks for question answering
- Use Gemini / Google Generative AI for grounded responses
- Generate quizzes from uploaded study material
- Track quiz sessions and weak topics
- Multi-turn conversational Q&A — ask follow-up questions naturally, powered by Gemini's native chat API with per-subject conversation history

## Architecture

- `backend/` — FastAPI app, database models, document processing, embedding storage, and LLM integration
- `frontend/` — React + Vite user interface for subjects, uploads, QA chat, and quizzes

## Tech Stack

- Python 3.12+ (FastAPI, SQLAlchemy, ChromaDB, SentenceTransformers)
- React 19 + Vite
- Google Gemini SDK (`google-generativeai`)
- SQLite for app metadata and chat history
- ChromaDB for vector storage and retrieval

## Prerequisites

- Python 3.12+
- Node.js 20+ / npm
- A valid Gemini API key

## Backend Setup

1. Change to the backend folder:

```bash
cd backend
```

2. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in `backend/`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
CHROMA_PERSIST_DIR=./chroma_data
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_UPLOAD_SIZE_MB=20
```

4. Start the backend server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will initialize the SQLite database at `backend/study_companion.db` and persist embeddings under `backend/chroma_data`.

## Frontend Setup

1. Change to the frontend folder:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

4. Open the app in your browser at:

```text
http://localhost:5173
```

## Supported Upload Types

- `.pdf`
- `.pptx`

## How to Use

1. Create a subject
2. Upload a PDF or PPTX file for that subject
3. Ask questions in the Q&A panel
4. Generate quiz questions from your uploaded notes
5. Review quiz scores and weak topic data

## Backend API Endpoints

- `POST /subjects/` — create a new subject
- `GET /subjects/` — list subjects
- `GET /subjects/{subject_id}/files` — list files for a subject
- `DELETE /subjects/{subject_id}` — delete a subject and related collections
- `GET /subjects/dashboard` — dashboard stats and weak topics
- `POST /upload/` — upload a file to a subject
- `POST /qa/ask` — ask a question against a subject collection
- `POST /quiz/generate` — generate quiz questions from uploaded content

## Notes

- The backend uses a local SQLite file and ChromaDB persistence, so data remains across restarts.


