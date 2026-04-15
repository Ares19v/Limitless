<div align="center">
  <h1>Limitless 📄⚡</h1>
  <p><strong>Enterprise-Grade RAG Pipeline · Semantic PDF Intelligence · High-Performance Local AI</strong></p>
</div>

> **A production-ready Retrieval-Augmented Generation (RAG) system** engineered to parse, embed, and intelligently chat with any PDF document. Powered by the ultra-fast Groq LLM inference, Pinecone Vector Storage, and HuggingFace Local Embeddings for zero-cost, high-precision semantic search.

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

## 🛠️ Architecture & Tech Stack

Limitless is built with an aggressive focus on performance, modularity, and modern standards.

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | Vite 5, React 18, Tailwind CSS, Zustand | Optimal client-side performance, granular state management, and utility-first styling for a sleek, responsive UI. |
| **Backend** | Python 3.11+, FastAPI, Uvicorn | High-concurrency async request handling and robust OpenAPI schema generation. |
| **LLM Inference** | Groq Cloud (`llama-3.3-70b-versatile`) | LPU-powered inference providing unmatched Token-per-second (TPS) capabilities for real-time RAG. |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` | Open-source, local-first embedder. No monthly fees, no network latency, and high semantic density (384 dimensions). |
| **Document Processing** | `pypdf`, LangChain | Reliable, thread-safe PDF text extraction paired with semantic chunk splitting. |
| **Vector DB** | Pinecone | Serverless, highly-available vector store with namespace isolation per document. |
| **Metadata DB** | SQLite (`aiosqlite`) | Zero-setup, async-native edge database auto-created on application launch. |
| **Testing** | Pytest, Vitest, RTL | Comprehensive test suites ensuring pipeline reliability (All pipelines passing natively). |

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
