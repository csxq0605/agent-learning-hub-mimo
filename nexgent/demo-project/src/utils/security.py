"""JWT and password-hashing utilities.

Constants are module-level so they can be imported directly:

    from src.utils.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JWT_SECRET: str = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt and return the hash string."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the bcrypt *hashed* password."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(subject: str) -> str:
    """Create a short-lived access token.

    Claims:
        sub  — the user id (as a string)
        exp  — expiration timestamp (UTC)
        type — "access"
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh token.

    Claims:
        sub  — the user id (as a string)
        exp  — expiration timestamp (UTC)
        type — "refresh"
        jti  — unique token id (UUID v4) used for per-token revocation
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Token decoding
# ---------------------------------------------------------------------------

def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT.  Raises ``jwt.PyJWTError`` on failure."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# Blacklist helpers  (TODO — not yet implemented)
# ---------------------------------------------------------------------------

def is_token_blacklisted(jti: str) -> bool:  # TODO
    """Check whether a token's *jti* has been revoked.

    This should query the ``token_blacklist`` table.

    Currently returns ``False`` (no token is considered revoked).
    """
    return False


def blacklist_token(jti: str, user_id: int, expires_at: datetime) -> None:  # TODO
    """Add a token *jti* to the blacklist.

    Should INSERT a row into ``token_blacklist`` with the given *jti*,
    *user_id*, and *expires_at*.

    Currently a no-op.
    """
    pass


def blacklist_all_user_tokens(user_id: int) -> int:  # TODO
    """Revoke every refresh token belonging to *user_id*.

    Implementation strategy (pick one):
      1. INSERT blacklist rows for every known jti for this user.
      2. Maintain a ``token_epoch`` on the User model and reject tokens
         issued before the epoch.

    Should return the number of tokens revoked.

    Currently returns 0.
    """
    return 0
