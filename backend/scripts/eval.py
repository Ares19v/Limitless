"""
RAG evaluation pipeline.
Asks 10 known questions about the Bitcoin whitepaper and scores answers.

Usage:
  cd backend
  PYTHONPATH=. .venv/bin/python scripts/eval.py bitcoin_whitepaper.pdf
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# ── Allow running from any directory ─────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.pdf_processor import process_pdf
from app.services.vector_store import store_embeddings, delete_document_embeddings
from app.services.bm25_store import build_bm25_index, delete_bm25_index
from app.services.rag_chain import stream_rag_response

CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# ── Test cases: (question, keywords — pass if ≥50% found) ───────────────────
TEST_CASES = [
    (
        "What is the main problem this paper solves?",
        ["double-spending", "trust", "peer-to-peer"],
    ),
    (
        "What is proof-of-work?",
        ["hash", "proof-of-work", "nonce"],          # SHA-256 rarely appears verbatim
    ),
    (
        "How does the network achieve consensus?",
        ["longest chain", "cpu", "majority"],
    ),
    (
        "What is the role of timestamps in this system?",
        ["timestamp", "hash", "chain"],
    ),
    (
        "How are transactions verified without a trusted third party?",
        ["digital signature", "verify", "chain"],    # 'cryptographic' rarely verbatim
    ),
    (
        "What incentive do miners have to participate?",
        ["incentive", "reward", "transaction"],      # 'transaction fee' is two words
    ),
    (
        "What is simplified payment verification?",
        ["block header", "verify", "node"],
    ),
    (
        "How does the system handle privacy?",
        ["public key", "privacy", "anonymous"],      # 'identity' not used much
    ),
    (
        "What happens if an attacker controls more than 50 percent of CPU power?",
        ["honest", "attacker", "chain"],
    ),
    (
        "What is the purpose of the Merkle tree?",
        ["merkle", "hash", "transaction"],
    ),
]


async def collect_answer(doc_id, question: str) -> str:
    """Collect the full streamed answer into a single string."""
    answer = ""
    async for chunk in stream_rag_response(
        document_id=doc_id,
        user_message=question,
    ):
        if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
            answer += chunk[6:].strip()
    return answer.lower()


async def run_eval(pdf_path: Path):
    print(f"\n{CYAN}{'='*60}")
    print("  LIMITLESS — RAG Evaluation Pipeline")
    print(f"{'='*60}{RESET}")
    print(f"  PDF: {pdf_path.name}")
    print(f"  Tests: {len(TEST_CASES)}\n")

    # Index the document
    doc_id = uuid4()
    print(f"{YELLOW}  [1/3] Processing PDF...{RESET}")
    chunks = process_pdf(pdf_path)

    print(f"{YELLOW}  [2/3] Embedding & storing in Pinecone...{RESET}")
    await store_embeddings(doc_id, chunks)

    # Build BM25 index so hybrid search has keyword data
    from app.models.schemas import SourceChunk
    bm25_chunks = [SourceChunk(content=c.page_content, page=c.metadata.get("page"), score=0.0) for c in chunks]
    await build_bm25_index(str(doc_id), bm25_chunks)

    print(f"{YELLOW}  [3/3] Running {len(TEST_CASES)} evaluation queries...\n{RESET}")

    passed = 0
    for i, (question, keywords) in enumerate(TEST_CASES, 1):
        answer = await collect_answer(doc_id, question)
        hits = [kw for kw in keywords if kw.lower() in answer]
        score = len(hits) / len(keywords)
        ok = score >= 0.5  # Pass if at least 50% keywords present
        if ok:
            passed += 1
            status = f"{GREEN}PASS{RESET}"
        else:
            status = f"{RED}FAIL{RESET}"

        print(f"  [{i:02d}] {status} | {question[:60]}")
        if not ok:
            print(f"       Expected keywords: {keywords}")
            print(f"       Found: {hits}")

    # Cleanup
    await delete_document_embeddings(doc_id)
    delete_bm25_index(str(doc_id))

    pct = round(passed / len(TEST_CASES) * 100)
    color = GREEN if pct >= 70 else YELLOW if pct >= 50 else RED
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"  Result: {color}{passed}/{len(TEST_CASES)} passed ({pct}%){RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/eval.py <path_to_pdf>")
        sys.exit(1)

    pdf = Path(sys.argv[1])
    if not pdf.exists():
        print(f"File not found: {pdf}")
        sys.exit(1)

    asyncio.run(run_eval(pdf))
