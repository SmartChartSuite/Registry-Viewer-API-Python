import os
import json
from typing import Dict, Set
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, status

# JWKS caching
_jwks_cache: Dict = {}

def get_jwks_url() -> str:
    """Return the JWKS endpoint URL for the configured Auth0 tenant.
    Allows override via OAUTH2_JWKS_URL env var for testing.
    """
    return os.getenv(
        "OAUTH2_JWKS_URL",
        f"https://{os.getenv('AUTH_DOMAIN')}/.well-known/jwks.json",
    )

async def fetch_jwks() -> Dict:
    """Fetch the JWKS from Auth and cache it for the lifetime of the process."""
    global _jwks_cache
    if not _jwks_cache:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(get_jwks_url())
                resp.raise_for_status()
                _jwks_cache = resp.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to fetch JWKS: {str(exc)}",
            ) from exc
        except ValueError as exc:  # JSON decoding error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Invalid JWKS response",
            ) from exc
    return _jwks_cache

async def verify_jwt(token: str) -> Dict:
    """Verify an Auth‑issued JWT.
    Returns the decoded payload (including the `scope` claim) if verification passes.
    Raises HTTPException(401) on any failure.
    """
    print(f"DEBUG verify_jwt: Received token: {token[:50]}...")  # Debug
    jwks = await fetch_jwks()
    print(f"DEBUG verify_jwt: Fetched JWKS with {len(jwks.get('keys', []))} keys")  # Debug
    # Decode header to obtain the key ID (kid)
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        print(f"DEBUG verify_jwt: Token KID: {kid}")  # Debug
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
        print(f"DEBUG verify_jwt: No matching key found for KID: {kid}")  # Debug
        print(f"DEBUG verify_jwt: Available KIDs: {[k.get('kid') for k in jwks.get('keys', [])]}")  # Debug
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find matching JWK",
        )

    public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=os.getenv("AUTH_AUDIENCE"),
            issuer=f"https://{os.getenv('AUTH_DOMAIN')}/",
            options={"verify_aud": bool(os.getenv('AUTH_AUDIENCE'))},
        )
        print(f"DEBUG verify_jwt: Token verified successfully. Payload: {payload}")  # Debug
        return payload
    except jwt.PyJWTError as exc:
        print(f"DEBUG verify_jwt: JWT decode failed: {exc}")  # Debug
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token",
        ) from exc
