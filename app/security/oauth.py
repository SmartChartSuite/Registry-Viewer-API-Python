import os
import json
from typing import Dict, Set
import httpx
import jwt
from fastapi import HTTPException, status

# JWKS caching
_jwks_cache: Dict = {}

def get_jwks_url() -> str:
    """Return the JWKS endpoint URL for the configured Auth0 tenant.
    Allows override via OAUTH2_JWKS_URL env var for testing.
    """
    return os.getenv(
        "OAUTH2_JWKS_URL",
        f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/jwks.json",
    )

async def fetch_jwks() -> Dict:
    """Fetch the JWKS from Auth0 and cache it for the lifetime of the process."""
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient() as client:
            resp = await client.get(get_jwks_url())
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache

async def verify_jwt(token: str) -> Dict:
    """Verify an Auth0‑issued JWT.
    Returns the decoded payload (including the `scope` claim) if verification passes.
    Raises HTTPException(401) on any failure.
    """
    jwks = await fetch_jwks()
    # Decode header to obtain the key ID (kid)
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        ) from exc

    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'kid' header",
        )

    # Find the matching JWK
    key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find matching JWK",
        )

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_data))
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=os.getenv("AUTH0_AUDIENCE"),
            issuer=f"https://{os.getenv('AUTH0_DOMAIN')}/",
            options={"verify_aud": bool(os.getenv('AUTH0_AUDIENCE'))},
        )
        return payload
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token",
        ) from exc
