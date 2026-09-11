-- Devil's Advocate Panel Database Schema
-- Run this in your Supabase SQL editor

-- Enable pgvector extension for RAG benchmark embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Sessions table
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    pitch_text TEXT NOT NULL,
    intensity VARCHAR(20) NOT NULL DEFAULT 'normal',
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, completed, abandoned
    round_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Transcript entries
CREATE TABLE IF NOT EXISTS public.transcript_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.sessions(id) ON DELETE CASCADE,
    persona VARCHAR(20) NOT NULL,
    round INT NOT NULL,
    thinking_text TEXT,
    question_text TEXT NOT NULL,
    user_reply TEXT,
    provider_used VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Verdicts
CREATE TABLE IF NOT EXISTS public.verdicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES public.sessions(id) ON DELETE CASCADE,
    weaknesses JSONB NOT NULL DEFAULT '[]'::jsonb,
    pdf_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. User connections (OAuth tokens for GitHub, Stripe, Sheets, Notion)
CREATE TABLE IF NOT EXISTS public.user_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL, -- github, stripe, google_sheets, notion
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, provider)
);

-- 5. Benchmark corpus (RAG for financial analyst and market realist)
CREATE TABLE IF NOT EXISTS public.benchmark_corpus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(768), -- Gemini embedding text-embedding-004 is 768 dimensions
    source VARCHAR(255),
    tag VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_transcript_session_id ON public.transcript_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_user_connections_user_id ON public.user_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_corpus_tag ON public.benchmark_corpus(tag);

-- Row Level Security (RLS)
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcript_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verdicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.benchmark_corpus ENABLE ROW LEVEL SECURITY;

-- Sessions policies
CREATE POLICY "Users can manage own sessions" ON public.sessions
    FOR ALL USING (auth.uid() = user_id);

-- Transcript policies
CREATE POLICY "Users can read/write transcripts for own sessions" ON public.transcript_entries
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.sessions s 
            WHERE s.id = transcript_entries.session_id AND s.user_id = auth.uid()
        )
    );

-- Verdicts policies
CREATE POLICY "Users can access verdicts for own sessions" ON public.verdicts
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.sessions s 
            WHERE s.id = verdicts.session_id AND s.user_id = auth.uid()
        )
    );

-- User connections policies
CREATE POLICY "Users can manage own connections" ON public.user_connections
    FOR ALL USING (auth.uid() = user_id);

-- Benchmark corpus policies (read-only to all authenticated users)
CREATE POLICY "Authenticated users can read benchmark corpus" ON public.benchmark_corpus
    FOR SELECT USING (auth.role() = 'authenticated');
