"""Supabase client singleton for G-Nome backend."""

import os
from supabase import create_client, Client

_client: Client | None = None


def get_supabase() -> Client | None:
    """Return Supabase client, or None if not configured."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return None

    _client = create_client(url, key)
    return _client
