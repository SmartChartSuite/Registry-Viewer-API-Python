# AGENTS Guidance – Python API Service

## Repository Overview
- **docs/** – contains the OpenAPI spec (`api-docs.yaml`) and the SQL definition files that describe the PostgreSQL schema.
- No source code is present yet; the repository is a starting point for building the backend service.

## Goal
Create a runnable Python API that implements the operations described in `docs/api-docs.yaml` against a PostgreSQL database using SQLAlchemy as the ORM.

## Recommended Tech Stack
| Layer | Recommendation |
|------|-----------------|
| **Web framework** | **FastAPI** (async‑first, automatic OpenAPI generation, Pydantic models) – can be swapped for Flask if desired |
| **ORM** | SQLAlchemy 2.x (declarative mapping) with async support (`asyncpg` driver) |
| **Database** | PostgreSQL (any version ≥ 12) |
| **Migrations** | Alembic (integrates with SQLAlchemy) |
| **Testing** | pytest + httpx (or FastAPI's `TestClient`) |
| **OpenAPI generation** | The existing `docs/api-docs.yaml` can be used as source‑of‑truth for request/response schemas. FastAPI can export an up‑to‑date spec from the implemented routes. |
| **Code generation (optional)** | `openapi-python-client` or `openapi-generator-cli` can scaffold client stubs, but the server implementation will be handwritten to match the DB model. |

## High‑Level Workflow
1. **Initialize a Python project** (`poetry init` or `pipenv`) and add dependencies (`fastapi`, `uvicorn`, `sqlalchemy[async]`, `psycopg2-binary`/`asyncpg`, `alembic`, `pydantic`, `pytest`).
2. **Translate the SQL schema to SQLAlchemy models**.  For each table, generate a declarative class with column types matching the SQL definitions. For views, generate read‑only models (set `__mapper_args__ = {"primary_key": [<col>]}` if needed). Optionally use `sqlacodegen` to bootstrap the models, then hand‑tune them.
3. **Map OpenAPI schemas to Pydantic models**.  The `components/schemas` section of `docs/api-docs.yaml` already defines the JSON shapes. Create a `schemas/` package with `pydantic` classes that mirror those definitions (field names, types, example values). Use `from_orm=True` to let FastAPI serialize SQLAlchemy objects directly.
4. **Implement endpoint handlers**.  For each path in the OpenAPI spec, write a FastAPI route (`@router.get(...)`, `@router.post(...)`, etc.). Inside the handler, use an async `Session` to query or modify the ORM models, then return the appropriate Pydantic schema. Validate input parameters (`type`, `caseId`, etc.) according to the documentation you added earlier.
5. **Add authentication** – The service expects an Auth0‑issued **Bearer** token. If the `Authorization` header does not contain a Bearer token, the request falls back to **HTTP Basic** authentication using credentials defined by the `API_BASIC_USER` and `API_BASIC_PASSWORD` environment variables. Scopes are strings of the form `<action>:<registry>` (e.g. `read:syphilis`, `write:metadata`). The service enforces the required scope for each endpoint and returns **403 Forbidden** when a scope is missing.
6. **Run migrations** with Alembic whenever the DB model changes.
7. **Testing**
   - Write unit tests for each route using FastAPI’s `TestClient`.
   - Include integration tests that spin up a temporary PostgreSQL container (via `pytest‑docker` or `testcontainers`) and run the full query stack.
8. **Documentation**
   - FastAPI auto‑generates Swagger UI at `/docs` and ReDoc at `/redoc`.
   - Keep `docs/api-docs.yaml` as the canonical source; you can export FastAPI’s generated spec (`app.openapi()`) and compare it with the original file to ensure fidelity.

## Next Steps
- Review the draft `plan.md` (see the file in the repo) and confirm any preferences (e.g., FastAPI vs Flask, naming conventions, folder layout).
- Provide the mapping between the SQL tables/views and the OpenAPI components you’d like to enforce (e.g., `CaseData` ↔ `viewer.case` table). 
- Once approved, we will create the new `AGENTS.md`, scaffold the project, and start populating `plan.md` with concrete tasks.
