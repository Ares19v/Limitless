<div align="center">
  <h1>Limitless 📄⚡</h1>
  <p><strong>Production-Grade RAG Pipeline · Hybrid Search · Agent Mode · Multi-Document Intelligence</strong></p>
</div>

> **A full-stack Retrieval-Augmented Generation (RAG) system** engineered to parse, embed, and intelligently chat with any PDF document. Built with Groq LLM (ultra-fast inference), Pinecone vector storage, local HuggingFace embeddings, hybrid BM25+vector search, cross-encoder re-ranking, and a ReAct agent with real-time web search.

---

## Quick Start

### macOS / Linux
```bash
./start.sh
```

### Windows
```
Double-click start.bat
```

Both scripts:
1. Create a Python virtual environment and install all backend deps
2. Install frontend npm packages
3. Copy `.env.example` → `.env` if not present
4. Launch backend + frontend and open the browser

---

## First-Time Setup

Edit **`backend/.env`** (Groq key is **pre-filled**):

```env
GROQ_API_KEY=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

# Add your Pinecone key:
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

> ✅ No OpenAI key needed. Embeddings run **locally** via `sentence-transformers`.
> First startup downloads two models (~90MB + ~85MB, one-time only).

---

## v2 Features

### 🔍 Hybrid Search (BM25 + Pinecone Vector + RRF)
Every query runs **two searches simultaneously** — BM25 keyword scoring and semantic vector search — then fuses results using Reciprocal Rank Fusion (RRF). This combines keyword precision with semantic understanding, outperforming either approach alone.

### 🏆 Cross-Encoder Re-ranking
After retrieval, a `cross-encoder/ms-marco-MiniLM-L-6-v2` model re-scores and re-ranks every candidate chunk against your exact question. Only the top 5 are sent to the LLM — dramatically improving answer quality.

### 🤖 Agent Mode
A LangChain ReAct agent with three live tools:
- `🔍 search_document` — hybrid search in the current PDF
- `🌐 web_search` — real-time DuckDuckGo search (no API key needed)
- `🧮 calculate` — safe math evaluator

Intermediate tool calls stream live in the UI before the final answer appears.

### 🌐 Multi-Document Cross-Search
Toggle "All Docs" mode to ask a single question across **every uploaded document simultaneously** — no need to know which document has the answer.

### ✨ AI Document Summaries
Every PDF auto-generates a 3-bullet AI summary immediately after processing. Shown in the sidebar under each document with one click.

### 💾 Persistent Conversation Memory
Chat history is stored in SQLite per document. Close the tab, come back — your conversation is still there. Memory is automatically loaded as context for every new message.

### 📎 Citation Highlights
Click any source excerpt chip to expand the **full source text** in an inline drawer. See exactly what passage the AI used to generate its answer.

### 🧪 Evaluation Pipeline
Automated scoring script that asks 10 benchmark questions about a document and reports pass/fail with keyword coverage:
```bash
cd backend && PYTHONPATH=. .venv/bin/python scripts/eval.py ../bitcoin_whitepaper.pdf
```

---

## Project Structure

```
Limitless/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # upload, chat, global_chat, agent_chat, documents, history
│   │   ├── core/            # config, logging
│   │   ├── services/
│   │   │   ├── pdf_processor.py   # PDF parsing + chunking
│   │   │   ├── embeddings.py      # HuggingFace local embeddings
│   │   │   ├── vector_store.py    # Pinecone + hybrid search + RRF
│   │   │   ├── bm25_store.py      # Local BM25 keyword index
│   │   │   ├── reranker.py        # Cross-encoder re-ranker
│   │   │   ├── rag_chain.py       # Full v2 RAG pipeline + summaries
│   │   │   ├── agent.py           # ReAct agent with 3 tools
│   │   │   └── document_store.py  # SQLite (documents + chat history)
│   │   ├── models/          # Pydantic schemas
│   │   └── utils/           # File handler
│   ├── scripts/
│   │   └── eval.py          # RAG evaluation pipeline
│   ├── tests/               # Pytest test suite
│   └── migrations/          # SQL migration guide
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow/  # Agent mode, Global mode, Citation drawer
│   │   │   ├── Sidebar/     # AI summary panel per document
│   │   │   ├── FileUpload/
│   │   │   └── Layout/
│   │   ├── hooks/           # useChat, useUpload, useDocuments
│   │   ├── lib/             # API client (history, agent, global chat)
│   │   ├── store/           # Zustand state
│   │   └── types/           # TypeScript interfaces
│   └── banner.mjs           # Cyan ASCII banner on npm run dev
│
├── start.sh                 # macOS/Linux one-click launcher
├── start.bat                # Windows one-click launcher
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Backend health check |
| `POST` | `/api/v1/upload` | Upload a PDF (multipart) |
| `GET` | `/api/v1/documents` | List all documents |
| `GET` | `/api/v1/documents/{id}` | Get document + summary |
| `DELETE` | `/api/v1/documents/{id}` | Delete doc + vectors + BM25 + history |
| `POST` | `/api/v1/chat/{id}` | Standard RAG chat (SSE stream) |
| `POST` | `/api/v1/chat/global` | Cross-document search (SSE stream) |
| `POST` | `/api/v1/agent/{id}` | Agent mode with tools (SSE stream) |
| `GET` | `/api/v1/history/{id}` | Get conversation history |
| `DELETE` | `/api/v1/history/{id}` | Clear conversation history |

Interactive docs: `http://localhost:8000/docs`

---

## Running Tests

### Backend
```bash
cd backend
PYTHONPATH=. .venv/bin/pytest tests/ -v --cov=app --cov-report=term-missing
```

### RAG Evaluation
```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/eval.py ../bitcoin_whitepaper.pdf
```

### Frontend
```bash
cd frontend && npm test
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
| `EMBEDDING_MODEL` | | `all-MiniLM-L6-v2` | Local HuggingFace embedder |
| `CHUNK_SIZE` | | `1000` | PDF chunk size (chars) |
| `CHUNK_OVERLAP` | | `200` | Chunk overlap |
| `TOP_K_RESULTS` | | `5` | Final results after re-ranking |
| `MAX_UPLOAD_SIZE_MB` | | `50` | Max PDF upload size |
| `ALLOWED_ORIGINS` | | `http://localhost:5173` | CORS origins |

### Frontend (`frontend/.env`)
| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | | `http://localhost:8000` | Backend URL |

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | Vite 5, React 18, Tailwind CSS, Zustand | Fast HMR, fine-grained reactivity, utility-first styling |
| **Backend** | FastAPI, Uvicorn, Python 3.11+ | Async-first, high-concurrency, auto OpenAPI docs |
| **LLM** | Groq Cloud `llama-3.3-70b-versatile` | LPU inference — fastest available token throughput |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` | Local, zero-cost, 384-dimensional semantic vectors |
| **Vector DB** | Pinecone (serverless) | Namespace-isolated, scalable ANN search |
| **Keyword Search** | `rank-bm25` (local) | BM25 index per document for hybrid retrieval |
| **Hybrid Fusion** | Reciprocal Rank Fusion (RRF) | State-of-the-art multi-source result merging |
| **Re-ranking** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Precision re-scoring of retrieval candidates |
| **Agent** | LangChain ReAct + DuckDuckGo | Tool-using AI with web search and math capabilities |
| **Metadata DB** | SQLite (`aiosqlite`) | Zero-setup async DB for documents + chat history |
| **PDF Parsing** | `pypdf` + LangChain splitters | Pure Python, cross-platform, thread-safe |
| **Testing** | Pytest + Vitest | Full backend + frontend coverage |

---

## Feature Comparison

| Feature | Basic RAG | **Limitless v2** |
|---|---|---|
| Search type | Vector only | Hybrid (BM25 + Vector + RRF) |
| Result quality | Raw retrieval | Cross-encoder re-ranked |
| Multi-document | ❌ | ✅ |
| Web search | ❌ | ✅ (Agent Mode) |
| Calculator | ❌ | ✅ (Agent Mode) |
| Auto-summary | ❌ | ✅ |
| Persistent history | ❌ | ✅ (SQLite) |
| Citation highlights | Basic | Full excerpt drawer |
| Evaluation | ❌ | ✅ (10-question pipeline) |
