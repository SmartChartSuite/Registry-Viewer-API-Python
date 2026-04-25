from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Callable

from .oauth import verify_jwt
from .basic import verify_basic
from .permissions import has_scope

# Global bearer scheme (do not auto‑error; we handle fallback)
_bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """Return a dict containing authentication info and scopes.
    Preference order: Bearer token → Basic auth.
    Raises 401 if no valid credentials are provided.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer realm=\"access\", Basic realm=\"access\""},
        )

    # Bearer token takes precedence if present and correctly parsed by the scheme
    if bearer:
        payload = await verify_jwt(bearer.credentials)
        scopes = set(payload.get("scope", "").split())
        return {"auth_method": "bearer", "scopes": scopes, "claims": payload}

    # Fallback to Basic auth
    if auth_header.lower().startswith("basic"):
        return verify_basic(auth_header)

    # Unsupported scheme
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unsupported authentication scheme",
        headers={"WWW-Authenticate": "Bearer, Basic"},
    )

def get_registry_param(registry: str | None = None) -> str:
    """Extract the registry identifier for scope checks.
    FastAPI will inject the path parameter `registry` here if it exists.
    If the endpoint does not have a `{registry}` path param (e.g., /metadata),
    we default to the literal string "metadata" which matches the special
    scope `read:metadata` / `write:metadata`.
    """
    return registry or "metadata"

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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope '{action}:{registry}'",
            )
    return _checker
