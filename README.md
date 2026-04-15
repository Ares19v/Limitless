# DocuMind 📄🤖 v2

> **Production-ready PDF RAG application — Groq LLM + Pinecone + HuggingFace Embeddings**  
> Upload any PDF · Ask questions · Get AI-powered, cited answers

---

## Quick Start

### macOS / Linux
```bash
# 1. Double-click start.sh  OR run:
./start.sh
```

### Windows (HP Omen)
```
Double-click start.bat
```

Both scripts will:
1. Create a Python virtual environment and install backend deps
2. Install frontend npm packages
3. Copy `.env.example` → `.env` if not present
4. Launch backend + frontend and open the browser automatically

---

## First-Time Setup

Edit **`backend/.env`** (the Groq key is **already filled in**):

```env
# Already set:
GROQ_API_KEY=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

# You only need to add this:
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX_NAME=documind
```

### Getting Your Pinecone Key (2 minutes)
1. Go to **[pinecone.io](https://www.pinecone.io)** → Sign Up Free
2. Dashboard → **Indexes** → **Create Index**
   - Name: `documind`
   - Dimensions: `384`
   - Metric: `cosine`
   - Cloud: `AWS`, Region: `us-east-1`
3. Dashboard → **API Keys** → copy your key
4. Paste into `backend/.env`

> ✅ No OpenAI key needed! Embeddings run locally via `sentence-transformers`.
> First startup downloads the model (~90MB, one-time only).

---

## Project Structure

```
DocuMind/
├── backend/          # FastAPI + LangChain + pgvector
│   ├── app/
│   │   ├── api/routes/   # upload, chat, documents
│   │   ├── core/         # config, logging
│   │   ├── services/     # pdf_processor, embeddings, vector_store, rag_chain
│   │   ├── models/       # Pydantic schemas
│   │   └── utils/        # cross-platform file handler
│   ├── tests/            # Pytest test suite
│   └── migrations/       # SQL migration for Supabase
│
├── frontend/         # Vite + React + TypeScript + Tailwind + Shadcn
│   ├── src/
│   │   ├── components/   # FileUpload, ChatWindow, Sidebar, Layout
│   │   ├── hooks/        # useChat, useUpload, useDocuments
│   │   ├── lib/          # API client, utilities
│   │   ├── store/        # Zustand state
│   │   └── types/        # TypeScript interfaces
│   └── tests/            # Vitest component tests
│
├── start.bat         # Windows one-click launcher
├── start.sh          # macOS/Linux one-click launcher
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Backend health check |
| `POST` | `/api/v1/upload` | Upload a PDF (multipart) |
| `GET` | `/api/v1/documents` | List all documents |
| `GET` | `/api/v1/documents/{id}` | Get document by ID |
| `DELETE` | `/api/v1/documents/{id}` | Delete document + embeddings |
| `POST` | `/api/v1/chat/{id}` | Chat (returns SSE stream) |

Interactive docs available at `http://localhost:8000/docs`

---

## Running Tests

### Backend
```bash
cd backend
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

### Frontend
```bash
cd frontend
npm test
```

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | *pre-filled* | Groq Cloud API key |
| `PINECONE_API_KEY` | ✅ | — | Pinecone API key |
| `PINECONE_INDEX_NAME` | | `documind` | Pinecone index name |
| `LLM_MODEL` | | `llama-3.3-70b-versatile` | Groq model |
| `EMBEDDING_MODEL` | | `all-MiniLM-L6-v2` | Local HuggingFace model |
| `CHUNK_SIZE` | | `1000` | PDF chunk size (chars) |
| `CHUNK_OVERLAP` | | `200` | Chunk overlap |
| `TOP_K_RESULTS` | | `5` | Similarity search results |
| `MAX_UPLOAD_SIZE_MB` | | `50` | Max PDF upload size |
| `ALLOWED_ORIGINS` | | `http://localhost:5173` | CORS origins |

### Frontend (`frontend/.env`)
| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | | `http://localhost:8000` | Backend URL |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vite 5 · React 18 · TypeScript · Tailwind CSS · Zustand |
| Backend | FastAPI · Uvicorn · Python 3.11+ |
| LLM | Groq Cloud (`llama-3.3-70b-versatile`) — ultra fast |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` — **free, runs locally** |
| PDF Parsing | pypdf (pure Python, cross-platform) |
| Vector DB | Pinecone (serverless, namespaced per document) |
| Metadata DB | SQLite (auto-created locally via aiosqlite) |
| Streaming | Server-Sent Events (SSE) |
| Testing | Pytest · Vitest · RTL |

---

## Features

- 📁 **Drag-and-drop PDF upload** with progress bar and queue
- 📊 **Processing status** — live polling until document is indexed
- 💬 **Streaming chat** — real-time token-by-token responses
- 📑 **Source citations** — every answer shows source page & similarity score
- 🌙 **Dark / Light mode** — auto-detects system preference
- 🗑️ **Document management** — delete documents and all embeddings
- 🔒 **Rate limiting** & file size validation on uploads
- 📝 **Interactive API docs** at `/docs` (Swagger UI)
- 🧪 **Full test suite** — Pytest (backend) + Vitest (frontend)
