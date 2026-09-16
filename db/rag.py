"""RAG retrieval logic for benchmark corpus in Supabase (pgvector)."""

from __future__ import annotations

from typing import Any
from .client import get_supabase_client
from core.config import get_secret
from core.timing import timed_stage

_embeddings_client = None


def _create_embeddings_client_raw(api_key: str) -> Any:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
        output_dimensionality=768,
    )


try:
    import streamlit as st
    _get_cached_embeddings = st.cache_resource(show_spinner=False)(_create_embeddings_client_raw)
except Exception:
    _get_cached_embeddings = _create_embeddings_client_raw


def get_embedding(text: str) -> list[float] | None:
    """Generate embedding vector using Google Gemini embeddings if available."""
    api_key = get_secret("GOOGLE_API_KEY")
    if not api_key:
        print("Warning: GOOGLE_API_KEY not set, cannot generate embedding.")
        return None
    try:
        with timed_stage("Embedding generation"):
            embeddings = _get_cached_embeddings(api_key)
            return embeddings.embed_query(text)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def retrieve_benchmarks(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Retrieve top relevant benchmark entries via pgvector similarity search or fallback."""
    with timed_stage(f"RAG retrieve_benchmarks (query='{query[:30]}...')"):
        return _retrieve_benchmarks_inner(query, top_k)


def _retrieve_benchmarks_inner(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return [
            {
                "content": "SaaS benchmarks: Median seed stage CAC payback is 12-18 months. Gross margin benchmark is 75-80%.",
                "source": "OpenView SaaS Benchmarks",
                "tag": "saas",
            }
        ]

    emb = get_embedding(query)
    if emb:
        try:
            # RPC call to custom similarity function if defined in Supabase
            res = client.rpc(
                "match_benchmark_corpus",
                {"query_embedding": emb, "match_threshold": 0.7, "match_count": top_k},
            ).execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"RPC match_benchmark_corpus failed or not installed, falling back to simple select: {e}")

    # Fallback to direct select
    try:
        res = client.table("benchmark_corpus").select("content, source, tag").limit(top_k).execute()
        if res.data:
            return res.data
    except Exception as e:
        print(f"Error retrieving benchmarks: {e}")

    return [
        {
            "content": "Startup failure study: 42% of startups fail due to lack of market need, 29% run out of cash.",
            "source": "CB Insights Post-Mortem",
            "tag": "post_mortem",
        }
    ]
