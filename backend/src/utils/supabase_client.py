"""Supabase client singleton for admin operations."""
from typing import Optional

from supabase import Client, create_client

from ..config import get_settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client with service key (admin access).

    Returns:
        Client: Supabase client instance

    Raises:
        ValueError: If Supabase credentials are not configured
    """
    global _supabase_client

    if _supabase_client is None:
        settings = get_settings()

        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError(
                "Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY"
            )

        _supabase_client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )

    return _supabase_client


def get_anon_client() -> Client:
    """Get Supabase client with anon key (public access).

    Returns:
        Client: Supabase client instance with anon key

    Raises:
        ValueError: If Supabase credentials are not configured
    """
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_anon_key:
        raise ValueError(
            "Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY"
        )

    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_anon_key,
    )
