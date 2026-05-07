import os
from dotenv import load_dotenv
from .logging_config import logger
load_dotenv()  # Load .env at startup
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from app.security.deps import get_current_user
from app.api.v1 import metadata, case_record, questions, search_cases, llm_query
from app.db.base import engine
from sqlalchemy import text
from app.config import DATA_SCHEMA, SCD_DATA_SCHEMA

app = FastAPI(
    title="SMART-PACER Registry Viewer API",
    version="v1.11.1",
    description="FastAPI implementation of the SMART-PACER Registry Viewer API",
)

# ---------------------------------------------------------------------------
# OpenAPI spec serving at root ('/') – respects Accept header.
# ---------------------------------------------------------------------------
from pathlib import Path
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse
import yaml

_openapi_yaml: str = ""
_openapi_json: dict = {}

@app.on_event("startup")
async def _load_openapi_spec() -> None:
    """Load the OpenAPI YAML file once at startup.
    Also parse it into JSON for fast JSON responses.
    """
    spec_path = Path(__file__).resolve().parents[1] / "docs" / "api-docs.yaml"
    global _openapi_yaml, _openapi_json
    _openapi_yaml = spec_path.read_text(encoding="utf-8")
    _openapi_json = yaml.safe_load(_openapi_yaml) or {}

@app.get("/", include_in_schema=False)
async def root(request: Request) -> Response:
    """Return the OpenAPI specification.
    * YAML is returned by default (Content-Type: application/vnd.oai.openapi).
    * If the client sends `Accept: application/json`, JSON is returned.
    """
    # Lazy‑load in case startup event didn't run (e.g., during tests)
    global _openapi_yaml, _openapi_json
    if not _openapi_yaml:
        spec_path = Path(__file__).resolve().parents[1] / "docs" / "api-docs.yaml"
        _openapi_yaml = spec_path.read_text(encoding="utf-8")
        _openapi_json = yaml.safe_load(_openapi_yaml) or {}
    accept = request.headers.get("accept", "").lower()
    if "application/json" in accept:
        return JSONResponse(content=_openapi_json, media_type="application/json")
    return PlainTextResponse(content=_openapi_yaml, media_type="application/vnd.oai.openapi")

# OAuth2 security scheme (exposed in generated OpenAPI)
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{os.getenv('AUTH0_DOMAIN')}/authorize",
    tokenUrl=f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token",
    scopes={
        "read:syphilis": "Read data from the syphilis registry",
        "write:syphilis": "Write data to the syphilis registry",
        "read:scd": "Read data from the scd registry",
        "write:scd": "Write data to the scd registry",
        "read:metadata": "Read metadata entries",
        "write:metadata": "Create / modify metadata entries",
    },
)

# Include API routers
app.include_router(metadata.router, dependencies=[Depends(get_current_user)])
app.include_router(case_record.router, dependencies=[Depends(get_current_user)])
app.include_router(questions.router, dependencies=[Depends(get_current_user)])
app.include_router(search_cases.router, dependencies=[Depends(get_current_user)])
app.include_router(llm_query.router, dependencies=[Depends(get_current_user)])

# ---------------------------------------------------------------------------
# Global exception handling – log unhandled errors and return safe JSON responses
# ---------------------------------------------------------------------------
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Log client errors (4xx) as warnings; server errors (5xx) as errors
    if 400 <= exc.status_code < 500:
        logger.warning("%s %s – %d %s", request.method, request.url.path, exc.status_code, exc.detail)
    else:
        logger.error("%s %s – %d %s", request.method, request.url.path, exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s %s – %s", request.method, request.url.path, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

