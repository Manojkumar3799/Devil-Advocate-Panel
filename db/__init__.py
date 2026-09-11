"""Database package exports."""

from .client import get_supabase_client
from .sessions import create_session, update_session_status, get_user_sessions, get_session
from .transcripts import save_transcript_entry, get_session_transcript
from .verdicts import save_verdict, update_pdf_url, get_verdict
from .connections import save_user_connection, get_user_connections, get_connection, delete_connection
from .rag import retrieve_benchmarks

__all__ = [
    "get_supabase_client",
    "create_session",
    "update_session_status",
    "get_user_sessions",
    "get_session",
    "save_transcript_entry",
    "get_session_transcript",
    "save_verdict",
    "update_pdf_url",
    "get_verdict",
    "save_user_connection",
    "get_user_connections",
    "get_connection",
    "delete_connection",
    "retrieve_benchmarks",
]
