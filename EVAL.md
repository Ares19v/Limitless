# EVAL — Limitless RAG Pipeline

> **Evaluation Date:** 2026-05-29
> **Evaluator:** Automated Portfolio Review
> **Maturity Level:** Production-Ready (Maturity Score: 9.2/10)

---

## 1. Project Purpose & Problem Statement

Limitless is a state-of-the-art, production-grade Retrieval-Augmented Generation (RAG) system designed to deliver cited, highly precise, and low-latency answers from uploaded PDF documents. It addresses the common industry challenges of LLM hallucinations, high API inference latencies, and search inaccuracies by implementing a complete "v2" hybrid search architecture.

By combining dense vector search, sparse keyword indices, reciprocal rank fusion (RRF), cross-encoder re-ranking, and dynamic agent capabilities into a single cohesive system, Limitless demonstrates advanced RAG engineering expertise suited for enterprise-grade intelligence search and document interaction.

---

## 2. Technical Architecture & Tech Stack

Limitless uses a highly optimized full-stack microservice design:

```
                  ┌───────────────────────────────┐
                  │      React + Vite Client      │
                  └───────────────┬───────────────┘
                                  │ HTTP / SSE Stream
                                  ▼
                  ┌───────────────────────────────┐
                  │          FastAPI App          │
                  └───────────────┬───────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  rank-bm25    │           │ HuggingFace   │           │ ms-marco      │
│  Keyword Index│           │ MiniLM Embeds │           │ Cross-Encoder │
└───────────────┘           └───────┬───────┘           └───────────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │ Pinecone DB   │
                            └───────────────┘
```

- **Backend Architecture (FastAPI + Python 3.11):**
  - **PDF Parser (`pdf_processor.py`):** Dynamic semantic chunking with overlapping bounds (1000 characters, 200 overlap).
  - **Sparse Ingestion (`bm25_store.py`):** Generates a local `rank-bm25` index per document for keyword alignment.
  - **Dense Ingestion (`embeddings.py`):** Runs local inference using SentenceTransformers `all-MiniLM-L6-v2` (384-dimensional cosine similarity).
  - **Vector DB (`vector_store.py`):** Integrates Pinecone Serverless to persist high-dimensional document vectors.
  - **Reciprocal Rank Fusion (RRF):** Fuses dense vector scores and sparse BM25 ranks to compile 15 candidate matches.
  - **Re-ranking (`reranker.py`):** Leverages `cross-encoder/ms-marco-MiniLM-L-6-v2` locally to score candidates against the exact prompt, filtering down to the top 5 passages.
  - **Resiliency Manager (`key_manager.py`):** Controls a pool of Groq API keys with automated model fallback (`llama-3.3-70b` ➔ `llama-3.1-8b` ➔ `gemma2`) on HTTP 429 rate limit exceptions.
  - **AI ReAct Agent (`agent.py`):** Utilizes LangChain to support dynamic tool routing (Document Search, Live DuckDuckGo Web Search, Math Tools).
  - **Audit Trail:** SQLite database using `aiosqlite` stores metadata, document indices, and full chat histories.
- **Frontend Architecture (React 18 + Vite + Zustand):**
  - Uses Zustand for clean store management.
  - Supports SSE streaming for token-by-token visual rendering, side-by-side auto-summary sidebars, multi-document toggles, and expandable source citation drawers.

---

## 3. Core ML Models & Download Instructions

The system operates using local embedding and re-ranking pipelines to minimize API reliance and cost:

1. **Local Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (automatically downloaded to HuggingFace cache folder on first run).
2. **Local Re-ranking:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (automatically compiled and run locally via HuggingFace transformers).
3. **Primary LLM:** Groq Cloud LPU Inference running `llama-3.3-70b-versatile` (Requires a `GROQ_API_KEY` defined in `.env`).

---

## 4. Strengths

- **Elite Hybrid Search Architecture:** Combining BM25 + Vector Search + RRF + Cross-Encoder re-ranking represents the gold standard for RAG search precision.
- **Dynamic API Resiliency:** The Groq key pool manager and sequential model fallback engine (`llama-70b` ➔ `llama-8b` ➔ `gemma`) ensures absolute uptime even during heavy rate limits.
- **Self-Assessment Benchmarks:** Includes an automated evaluation suite (`scripts/eval.py`) that scores accuracy on target PDFs, outputting an intellectually honest validation report.
- **No-Bloat Client-Side Embedding:** Running embeddings and re-ranking completely locally on CPU/GPU keeps Pinecone serverless usage incredibly light and cost-effective.
- **Exceptional UI Execution:** Interactive text citations, automated bullet summaries on upload, and persistent histories deliver a clean product experience.

---

## 5. Limitations & Gaps

- **Local Re-Ranking CPU Bottleneck:** The `ms-marco` cross-encoder runs on-the-fly inside the FastAPI process. On multi-core systems, this can block or lag if multiple users upload files concurrently due to CPU computation peaks.
- **Memory BM25 Scale Limitations:** BM25 indices are stored as serialized local files. For massive documents or thousands of uploads, searching across all documents concurrently could increase disk I/O and RAM overhead.
- **ReAct Agent Loop Risks:** ReAct agents are prone to getting stuck in cyclic reasoning loops when given ambiguous user commands, exhausting API quotas.

---

## 6. Code Quality Assessment

- **Enterprise Structure:** High decoupling separating routes, ORMs, config schemas (`pydantic-settings`), custom middleware, and test suites.
- **Automated Validation:** Includes full Pytest coverage alongside RAG evaluation pipelines.

---

## 7. Maturity Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| Functionality | 9.5/10 | Exceptional feature set: agent tools, hybrid RAG, model pooling. |
| Code Quality | 9.5/10 | Exemplary clean architecture and rigorous typing. |
| Documentation | 9/10 | Detailed quickstart, environment breakdown, and evaluation report. |
| Scalability | 8.5/10 | Limited by local re-ranker CPU overhead and BM25 disk storage under massive user scale. |
| Security | 9.5/10 | Uses strict environmental keys, SQL injection resistance, and non-root Docker builds. |
| **Overall** | **9.2/10** | **Outstanding engineering.** Extremely mature and ready for serious production deployment. |

---

## 8. Suggested Next Steps

1. **Add Asynchronous Re-Ranker Worker:** Offload the local Cross-Encoder re-ranking process onto a Celery / Redis background worker queue to keep the FastAPI API event loop light and responsive under high user loads.
2. **Dynamic LLM-as-a-Judge Evaluation:** Upgrade `scripts/eval.py` to use an LLM-based evaluation framework (like Ragas or an LLM judge) instead of rigid keyword matching to handle semantic synonyms gracefully.
3. **Upgrade to Qdrant/Milvus:** Switch Pinecone to a local dockerized Qdrant or Milvus instance if offline enterprise RAG without external cloud dependencies is required.

---

<p align="center">Made by Devansh Tyagi @ 2026</p>
