from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from fastapi import Security
from typing import Callable
from ..logging_config import logger

from .oauth import verify_jwt
from .basic import verify_basic
from .permissions import has_scope

# Global bearer scheme (do not auto‑error; we handle fallback)
_bearer_scheme = HTTPBearer(auto_error=False)
# Global Basic scheme (do not auto‑error; we handle fallback)
_basic_scheme = HTTPBasic(auto_error=False)

async def get_current_user(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
    basic: HTTPBasicCredentials | None = Security(_basic_scheme),
) -> dict:
    """Return a dict containing authentication info and scopes.
    Preference order: Bearer token → Basic auth.
    Raises 401 if no valid credentials are provided.
    """
    # Prefer Bearer token if supplied
    if bearer:
        payload = await verify_jwt(bearer.credentials)
        scopes = set(payload.get("scope", "").split())
        return {"auth_method": "bearer", "scopes": scopes, "claims": payload}

    # If a Basic credential was parsed by FastAPI, validate it against env vars
    if basic:
        # Construct a header string compatible with verify_basic for reuse
        import base64
        cred_str = f"{basic.username}:{basic.password}".encode()
        header = "Basic " + base64.b64encode(cred_str).decode()
        return verify_basic(header)

    # No credentials provided – raise 401 with appropriate WWW-Authenticate header
    logger.warning(
        "Authentication failed: missing Authorization header from %s",
        request.client.host if request.client else "unknown",
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Authorization header",
        headers={"WWW-Authenticate": "Bearer realm=\"access\", Basic realm=\"access\""},
    )

def get_registry_param(registry: str | None = None) -> str:
    """Extract the registry identifier for scope checks.
    FastAPI will inject the path parameter `registry` here if it exists.
    If the endpoint does not have a `{registry}` path param (e.g., /metadata),
    we default to the literal string "metadata" which matches the special
    scope `read:metadata` / `write:metadata`.
    """
    return registry or "metadata"

# Helper for endpoints that *must* use the fixed "metadata" registry without exposing a query param.
def require_metadata_scope(action: str):
    """Dependency enforcing `<action>:metadata` scope without a `registry` query param.
    Uses the scopes defined in the environment (API_BASIC_SCOPES) for Basic auth.
    """
    async def _checker(user: dict = Depends(get_current_user)):
        if not has_scope(user["scopes"], action, "metadata"):
            logger.warning(
                "Authorization failure: user %s missing required scope '%s:metadata'",
                user.get("auth_method", "unknown"),
                action,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope '{action}:metadata'",
            )
    return _checker
def require_scope(action: str) -> Callable:
    """Dependency factory enforcing `<action>:<registry>` scope.
    Usage (per‑router or per‑endpoint):
        dependencies=[Depends(require_scope("read"))]
    """
    async def _checker(
        user: dict = Depends(get_current_user),
        registry: str = Depends(get_registry_param),
    ):
        if not has_scope(user["scopes"], action, registry):
            logger.warning(
                "Authorization failure: user %s missing required scope '%s:%s'",
                user.get("auth_method", "unknown"),
                action,
                registry,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope '{action}:{registry}'",
            )
    return _checker
