-- ============================================================
-- DocuMind v2 — Pinecone Setup Guide
-- (No SQL needed! This file is kept for reference only.)
-- ============================================================

-- The database has changed:
--   • Supabase + pgvector  →  REMOVED
--   • Pinecone             →  Vector storage (via SDK)
--   • SQLite               →  Document metadata (auto-created locally)

-- ── Pinecone Index Setup (do this ONCE in the Pinecone Dashboard) ──────────
--
-- 1. Go to https://www.pinecone.io → Sign Up Free
-- 2. Dashboard → Indexes → Create Index
-- 3. Settings:
--      Name:       documind
--      Dimensions: 384        (matches all-MiniLM-L6-v2 embedding model)
--      Metric:     cosine
--      Cloud:      AWS
--      Region:     us-east-1  (free tier region)
-- 4. Copy your API key from: Dashboard → API Keys
-- 5. Paste it into backend/.env as: PINECONE_API_KEY=...

-- ── SQLite (automatic) ─────────────────────────────────────────────────────
-- The app auto-creates a local SQLite database at:
--   backend/data/documind.db
-- Schema: documents table (id, filename, status, chunk_count, ...)
-- No manual setup needed — it happens on first startup.

-- ── That's it! ─────────────────────────────────────────────────────────────
-- Run: ./start.sh (Mac) or start.bat (Windows)
