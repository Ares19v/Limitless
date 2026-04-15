# Changelog

All notable changes to **Limitless** are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - April 2026 — *Production-Grade RAG*

### Added
- **Hybrid Search** — BM25 keyword index fused with Pinecone dense-vector search via Reciprocal Rank Fusion (RRF)
- **Cross-Encoder Re-ranking** — `ms-marco-MiniLM-L-6-v2` re-scores 15 candidates to final top 5
- **Agent Mode** — LangChain ReAct agent with 3 live tools: document search, web search (DuckDuckGo), and safe math evaluator
- **Multi-Document Global Search** — query across all uploaded PDFs simultaneously
- **AI Summaries** — auto-generated 3-bullet summary per document on upload, displayed in sidebar
- **Persistent Conversation Memory** — SQLite-backed chat history survives page reloads
- **Citation Highlights** — click any source chip to expand the full retrieved excerpt
- **RAG Evaluation Pipeline** — `scripts/eval.py` runs 10 benchmark queries and scores the pipeline (current: **8/10, 80%**)
- **Automatic Model Fallback** — on Groq 429 rate limits, system silently retries with `llama-3.1-8b-instant` → `gemma2-9b-it`
- **Groq Key Pool** — rotate across multiple API keys for higher token throughput
- **History API** — `GET /api/v1/history/{id}` and `DELETE /api/v1/history/{id}`
- **Global Chat API** — `POST /api/v1/chat/global`
- **Agent API** — `POST /api/v1/agent/{id}`

### Changed
- RAG pipeline now uses hybrid retrieval everywhere (was vector-only)
- Upload route now builds BM25 index and generates AI summary after embedding
- Document delete now cleans up BM25 index and chat history alongside Pinecone vectors
- Frontend ChatWindow rebuilt with Agent Mode toggle, Global Search toggle, and citation drawer

### Fixed
- Agent tools `asyncio.run()` crash inside running uvicorn event loop (fixed with thread pool)
- `/chat/global` route conflicting with `/{document_id}` route (fixed router registration order)
- BM25 index not built during eval script run

---

## [1.0.0] - March 2026 — *Initial Release*

### Added
- PDF upload with async background processing
- Pinecone vector storage with `all-MiniLM-L6-v2` local embeddings
- Groq `llama-3.3-70b-versatile` streaming via Server-Sent Events
- SQLite metadata store for documents
- React + Vite frontend with drag-and-drop upload
- Zustand state management
- One-click launcher scripts (`start.sh` / `start.bat`)
- Cyan ASCII banner on frontend dev start
