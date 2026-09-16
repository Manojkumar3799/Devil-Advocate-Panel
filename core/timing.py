"""Performance timing instrumentation for Devil's Advocate Panel."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Generator


def is_timing_enabled() -> bool:
    """Return True if timing logs are enabled via env var or session flag."""
    if os.environ.get("DEBUG_TIMING", "").lower() in ("true", "1", "yes"):
        return True
    try:
        import streamlit as st
        return bool(st.session_state.get("debug_timing", False))
    except Exception:
        return False


@contextmanager
def timed_stage(stage_name: str) -> Generator[None, None, None]:
    """Context manager measuring and logging the duration of a specific operation."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        if is_timing_enabled():
            print(f"[TIMING] {stage_name}: {elapsed_ms:.1f}ms ({elapsed_ms / 1000.0:.2f}s)")
