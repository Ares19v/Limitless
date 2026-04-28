<div align="center">

# Limitless

**Production-Grade RAG Pipeline for PDFs**

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Eval Score](https://img.shields.io/badge/RAG%20Eval-8%2F10%20(80%25)-brightgreen?style=flat-square)](EVALUATION_REPORT.md)
[![CI](https://github.com/Ares19v/limitless/actions/workflows/ci.yml/badge.svg)](https://github.com/Ares19v/limitless/actions/workflows/ci.yml)

*Upload any PDF. Ask anything. Get cited, accurate answers in real time.*

</div>

---

## What it does

Limitless is a full-stack Retrieval-Augmented Generation (RAG) system. Drop in any PDF, and the system parses, chunks, and embeds it locally. You then chat with it through a streaming UI backed by Groq's LPU inference — the fastest available LLM API.

**v2 goes further:** hybrid keyword+vector search, a cross-encoder re-ranker, an AI agent with live web search, multi-document querying, auto-summaries, persistent memory, and citation highlights — all backed by an automated evaluation pipeline.

---

## Features

| Feature | Description |
|---|---|
| **Hybrid Search** | BM25 keyword + Pinecone vector search fused via Reciprocal Rank Fusion |
| **Cross-Encoder Re-ranking** | `ms-marco-MiniLM-L-6-v2` re-ranks 15 candidates to top 5 |
| **Agent Mode** | ReAct agent with document search, live web search, and math tools |
| **Multi-Document Search** | Query across all uploaded PDFs simultaneously |
| **AI Summaries** | Auto 3-bullet summary generated on every upload |
| **Persistent Memory** | SQLite-backed conversation history survives page reloads |
| **Citation Highlights** | Expand any source chip to see the full retrieved passage |
| **Model Fallback** | Auto-switches `llama-70b → llama-8b → gemma2` on rate limits |
| **RAG Evaluation** | Automated 10-question benchmark pipeline (current: **80%**) |
| **Streaming** | Token-by-token streaming via Server-Sent Events |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vite 5, React 18, TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, Uvicorn, Python 3.11, aiosqlite |
| LLM | Groq Cloud `llama-3.3-70b-versatile` (LPU inference) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (runs locally, free) |
| Vector DB | Pinecone serverless (384-dim, cosine) |
| Keyword Search | `rank-bm25` local index per document |
| Re-ranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Agent | LangChain ReAct + DuckDuckGo Search |
| Metadata DB | SQLite via `aiosqlite` |

---

## Prerequisites

- **Python 3.11+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Pinecone account** (free) — [pinecone.io](https://www.pinecone.io)
- **Groq account** (free) — [console.groq.com](https://console.groq.com) *(API key pre-filled for quick start)*

---

## Installation

### Option A — One-click launcher (recommended)

```bash
# macOS / Linux
git clone https://github.com/Ares19v/limitless.git
cd limitless
chmod +x start.sh && ./start.sh
```

```batch
# Windows
git clone https://github.com/Ares19v/limitless.git
cd limitless
INSTALL.bat        :: First-time setup (run once)
Run_Project.bat    :: Start the app
```

The launcher automatically:
1. Creates a Python virtual environment
2. Installs all backend dependencies (CPU-only torch)
3. Installs frontend npm packages
4. Copies `.env.example` → `.env` and prompts for API keys
5. Starts both servers and opens the browser

> **Windows scripts:**
> - `INSTALL.bat` — First-time setup (run once)
> - `Run_Project.bat` — Start both servers and open the browser
> - `UNINSTALL.bat` — Remove local installation artifacts

---

### Option B — Docker (no Python/Node required)

```bash
git clone https://github.com/Ares19v/limitless.git
cd limitless
cp backend/.env.example backend/.env   # Fill in your API keys
docker compose up --build
```

Open **[http://localhost](http://localhost)** — the frontend proxies API calls to the backend automatically.

---

### Option B — Manual setup

#### 1. Clone the repo

```bash
git clone https://github.com/Ares19v/limitless.git
cd limitless
```

#### 2. Backend setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

#### 3. Configure environment variables

Edit `backend/.env`:

```env
# Groq — pre-filled, works immediately
GROQ_API_KEY=gsk_...

# Optional: add more keys to rotate across on rate limits
GROQ_API_KEY_POOL=key1,key2,key3,key4

# Pinecone — required
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=documind
```

**Getting your Pinecone key (2 minutes):**
1. [pinecone.io](https://pinecone.io) → Sign Up → Dashboard → **Create Index**
   - Name: `documind` · Dimensions: `384` · Metric: `cosine` · Cloud: `AWS us-east-1`
2. Dashboard → **API Keys** → copy key → paste into `.env`

> ✅ No OpenAI key needed. Embeddings run **locally** via HuggingFace (~90 MB, downloaded once on first run).

#### 4. Start the backend

```bash
cd backend
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)**

---

## Usage

1. **Upload** — drag a PDF onto the upload zone (max 50 MB)
2. **Wait** — status shows `Processing → Ready` (usually under 10 seconds)
3. **Chat** — type any question; the answer streams in real time with page citations
4. **Expand sources** — click any source chip to read the exact retrieved passage
5. **Agent mode** — toggle ⚡ Agent to enable live web search and math tools
6. **All Docs** — toggle 🌐 to search across every uploaded document at once

---

## API Reference

All endpoints are documented interactively at **`http://localhost:8000/docs`**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/upload` | Upload a PDF |
| `GET` | `/api/v1/documents` | List all documents |
| `GET` | `/api/v1/documents/{id}` | Get document + AI summary |
| `DELETE` | `/api/v1/documents/{id}` | Delete doc, vectors, index, history |
| `POST` | `/api/v1/chat/{id}` | Standard RAG chat (SSE stream) |
| `POST` | `/api/v1/chat/global` | Cross-document search (SSE stream) |
| `POST` | `/api/v1/agent/{id}` | Agent mode with tools (SSE stream) |
| `GET` | `/api/v1/history/{id}` | Get conversation history |
| `DELETE` | `/api/v1/history/{id}` | Clear conversation history |

---

## Running Tests

### Backend unit tests

```bash
cd backend
PYTHONPATH=. .venv/bin/pytest tests/ -v --cov=app --cov-report=term-missing
```

### RAG Evaluation Pipeline

```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/eval.py ../your_document.pdf
```

Current benchmark score: **8/10 (80%)** — see [EVALUATION_REPORT.md](EVALUATION_REPORT.md) for full analysis.

---

## Project Structure

```
limitless/
├── .github/workflows/
│   └── ci.yml               # GitHub Actions CI (backend + frontend)
├── backend/
│   ├── app/
│   │   ├── api/routes/          # upload, chat, global_chat, agent_chat, documents, history
│   │   ├── core/                # config (pydantic-settings), structured logging
│   │   ├── models/              # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── agent.py         # LangChain ReAct agent (3 tools)
│   │   │   ├── bm25_store.py    # Local BM25 keyword index
│   │   │   ├── document_store.py# SQLite (documents + chat history)
│   │   │   ├── embeddings.py    # HuggingFace local embeddings
│   │   │   ├── key_manager.py   # Groq key pool + model fallback
│   │   │   ├── pdf_processor.py # PDF parsing + chunking
│   │   │   ├── rag_chain.py     # Full v2 pipeline + summaries
│   │   │   ├── reranker.py      # Cross-encoder re-ranker
│   │   │   └── vector_store.py  # Pinecone + hybrid search + RRF
│   │   └── utils/
│   ├── scripts/
│   │   └── eval.py              # Automated RAG benchmark
│   ├── tests/                   # Pytest test suite
│   ├── Dockerfile
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow/      # Agent mode, Global mode, citation drawer
│   │   │   ├── FileUpload/
│   │   │   ├── Layout/
│   │   │   └── Sidebar/         # AI summary panel
│   │   ├── hooks/               # useChat, useUpload, useDocuments
│   │   ├── lib/                 # API client
│   │   ├── store/               # Zustand global state
│   │   └── types/               # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml           # Full stack with Docker
├── INSTALL.bat                  # Windows first-time setup
├── Run_Project.bat              # Windows launcher
├── UNINSTALL.bat                # Windows cleanup
├── start.sh                     # macOS/Linux one-click launcher
├── CHANGELOG.md
├── EVALUATION_REPORT.md
├── LICENSE
└── README.md
```

---

## Environment Variables

### `backend/.env`

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | *pre-filled* | Primary Groq API key |
| `GROQ_API_KEY_POOL` | | — | Comma-separated keys for rotation |
| `PINECONE_API_KEY` | ✅ | — | Pinecone API key |
| `PINECONE_INDEX_NAME` | | `documind` | Pinecone index name |
| `LLM_MODEL` | | `llama-3.3-70b-versatile` | Primary Groq model |
| `EMBEDDING_MODEL` | | `all-MiniLM-L6-v2` | Local embedding model |
| `CHUNK_SIZE` | | `1000` | Characters per PDF chunk |
| `CHUNK_OVERLAP` | | `200` | Overlap between chunks |
| `TOP_K_RESULTS` | | `5` | Final results after re-ranking |
| `MAX_UPLOAD_SIZE_MB` | | `50` | Max PDF size |
| `ALLOWED_ORIGINS` | | `http://localhost:5173` | CORS origins |

### `frontend/.env`

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend URL |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

```bash
# Fork → clone → create branch
git checkout -b feat/your-feature

# Make changes, then
git commit -m "feat: your feature description"
git push origin feat/your-feature
# Open PR
```

---

## License

[MIT](LICENSE) © 2026 Limitless Contributors
