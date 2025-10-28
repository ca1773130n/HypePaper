"""FastAPI dependencies for authentication and database."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..utils.supabase_client import get_anon_client

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Get current user from Supabase JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        User dict with 'id', 'email', etc. or None if no credentials/invalid

    Note:
        This function returns None for invalid tokens instead of raising 401
        to support optional authentication in endpoints like topics
    """
    if credentials is None:
        print("[AUTH DEBUG] No credentials provided")
        return None

    try:
        token = credentials.credentials
        print(f"[AUTH DEBUG] Token received: {token[:20]}..." if len(token) > 20 else f"[AUTH DEBUG] Token received: {token}")

        # Get Supabase settings for debugging
        from ..config import get_settings
        settings = get_settings()
        supabase_url = settings.supabase_url
        anon_key_prefix = settings.supabase_anon_key[:20] if settings.supabase_anon_key else "NOT_SET"

        print(f"[AUTH DEBUG] Backend Supabase URL: {supabase_url}")
        print(f"[AUTH DEBUG] Backend Anon Key (prefix): {anon_key_prefix}...")

        # Decode token header to check issuer (without verification)
        import base64
        import json
        try:
            # JWT format: header.payload.signature
            token_parts = token.split('.')
            if len(token_parts) >= 2:
                # Decode payload (add padding if needed)
                payload = token_parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded_payload = json.loads(base64.urlsafe_b64decode(payload))
                token_iss = decoded_payload.get('iss', 'unknown')
                token_aud = decoded_payload.get('aud', 'unknown')
                token_exp = decoded_payload.get('exp', 'unknown')
                print(f"[AUTH DEBUG] Token issuer (iss): {token_iss}")
                print(f"[AUTH DEBUG] Token audience (aud): {token_aud}")
                print(f"[AUTH DEBUG] Token expiry (exp): {token_exp}")

                # Check if token issuer matches backend Supabase URL
                if supabase_url and not token_iss.startswith(supabase_url):
                    print(f"[AUTH ERROR] Token issuer mismatch! Token from {token_iss} but backend expects {supabase_url}")
                    print(f"[AUTH ERROR] Frontend and backend are using DIFFERENT Supabase projects!")
        except Exception as decode_error:
            print(f"[AUTH DEBUG] Could not decode token for inspection: {decode_error}")

        # Use anon client to verify user JWT tokens (not service key)
        supabase = get_anon_client()
        print("[AUTH DEBUG] Anon client created")

        # Verify the JWT token
        user_response = supabase.auth.get_user(token)
        print(f"[AUTH DEBUG] User response: {user_response}")

        if not user_response or not user_response.user:
            print("[AUTH DEBUG] No user found in response")
            return None

        print(f"[AUTH DEBUG] User authenticated: {user_response.user.id}")
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "user_metadata": user_response.user.user_metadata,
        }
    except Exception as e:
        # Log the exception for debugging
        print(f"[AUTH DEBUG] Exception during authentication: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def get_current_user_required(
    user: Optional[dict] = Depends(get_current_user),
) -> dict:
    """Require authenticated user (raise 401 if not authenticated).

    Args:
        user: Current user from get_current_user

    Returns:
        User dict

    Raises:
        HTTPException: If user is not authenticated
    """
    if user is None:
        from ..config import get_settings
        settings = get_settings()

        error_detail = "Authentication required"

        # Add helpful debug info if Supabase is not properly configured
        if not settings.supabase_url or not settings.supabase_anon_key:
            error_detail = (
                "Authentication failed: Backend Supabase credentials not configured. "
                "Please check SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            )
            print(f"[AUTH ERROR] {error_detail}")
        else:
            error_detail = (
                "Authentication failed: Invalid or expired token. "
                "Please check that frontend and backend are using the same Supabase project. "
                "Server logs contain detailed debugging information."
            )
            print("[AUTH ERROR] Token validation failed - check server logs for details")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
        )
    return user


def get_user_id(user: dict = Depends(get_current_user_required)) -> UUID:
    """Extract user ID from authenticated user.

    Args:
        user: Authenticated user dict

    Returns:
        User ID as UUID
    """
    return UUID(user["id"])
