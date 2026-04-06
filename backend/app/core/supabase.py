"""Supabase client initialization."""

from supabase import Client, create_client

from app.core.config import settings


def get_supabase_client() -> Client:
    """Create and return a Supabase client using service role key."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)
