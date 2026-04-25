import os
import base64
from fastapi import HTTPException, status

def verify_basic(auth_header: str) -> dict:
    """Validate a Basic Authorization header.
    Returns a dict with the username and the set of scopes derived from
    the environment variable API_BASIC_SCOPES.
    """
    try:
        scheme, b64 = auth_header.split(" ", 1)
        if scheme.lower() != "basic":
            raise ValueError("Not a Basic auth header")
        decoded = base64.b64decode(b64).decode()
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed Basic auth header",
        )

    expected_user = os.getenv("API_BASIC_USER")
    expected_pass = os.getenv("API_BASIC_PASSWORD")
    if username != expected_user or password != expected_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Basic credentials",
        )

    # Scopes for the basic user come from a space‑separated env var
    scopes_str = os.getenv("API_BASIC_SCOPES", "")
    scopes = set(filter(None, scopes_str.split()))
    return {"username": username, "auth_method": "basic", "scopes": scopes}
