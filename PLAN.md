# Implementation Plan – FastAPI Service with Auth0 and Basic‑Auth

## 1. Project layout
```
PROJECT_ROOT/
├─ app/
│  ├─ main.py                # FastAPI instance, global deps
│  ├─ security/
│  │  ├─ __init__.py
│  │  ├─ oauth.py            # JWT verification, JWKS fetching
│  │  ├─ basic.py            # Basic‑Auth verification
│  │  ├─ permissions.py      # Scope parsing & checking
│  │  └─ deps.py             # Unified deps (user + registry)
│  ├─ db/
│  │  ├─ __init__.py
│  │  ├─ base.py             # async engine, SessionLocal, Base
│  │  └─ models/
│  │      ├─ __init__.py
│  │      └─ metadata.py     # SQLAlchemy model for `viewer.metadata`
│  ├─ api/
│  │  └─ v1/
│  │      ├─ __init__.py
│  │      └─ metadata.py     # Router for /metadata (read/write)
│  └─ schemas/
│      └─ __init__.py        # Pydantic models (generated from OpenAPI)
├─ alembic/                  # migrations (optional)
├─ docs/                     # OpenAPI spec + SQL schema files
│   ├─ api-docs.yaml
│   └─ *.sql
├─ tests/                    # unit & integration tests (future)
├─ .env.example
├─ PLAN.md                   # This file
├─ AGENTS.md                 # Updated guidance
└─ README.md                 # Project documentation
```

## 2. Environment variables
- `AUTH0_DOMAIN` – Auth0 tenant domain (e.g. `your-auth0-domain.auth0.com`).
- `AUTH0_AUDIENCE` – API identifier (`aud` claim) (e.g. `https://your-api-audience/`).
- `API_BASIC_USER` / `API_BASIC_PASSWORD` – credentials for Basic‑Auth fallback (example: `basic_user` / `basic_pass`).
- `API_BASIC_SCOPES` – space‑separated scopes granted to the Basic user (e.g. `read:syphilis write:metadata`).
- `DATABASE_HOST` – PostgreSQL host (e.g. `postgres.example.com`).
- `DATABASE_NAME` – Database name (e.g. `my_database`).
- `DATABASE_USER` – DB username (e.g. `my_user`).
- `DATABASE_PASSWORD` – DB password (e.g. `my_secret_password`).
- `DATABASE_URL` – **optional** full URL; if set it overrides the composed values (e.g. `postgresql+asyncpg://my_user:my_secret_password@postgres.example.com/my_database`).

## 3. Security modules
- **oauth.py** – builds JWKS URL, fetches and caches keys, verifies RS256 JWTs using `pyjwt`, extracts the `scope` claim.
- **basic.py** – decodes Basic header, validates against env vars, returns a set of scopes from `API_BASIC_SCOPES`.
- **permissions.py** – `has_scope(scopes, action, registry)` returns `True` if `<action>:<registry>` is present.
- **deps.py** –
  - `get_current_user` – unified dependency returning `{auth_method, scopes, sub?, username?}`.
  - `get_registry_param` – extracts `{registry}` path param or defaults to `'metadata'` for the `/metadata` endpoint.
  - `require_scope(action)` – FastAPI dependency that raises `403` when the required scope is missing.

## 4. FastAPI app (`app/main.py`)
- Creates `FastAPI` instance.
- Declares global dependency `Depends(get_current_user)`.
- Declares an `OAuth2AuthorizationCodeBearer` security scheme with all scopes (including the newly added `read:metadata`).
- Includes the `metadata` router (others can be added later).

## 5. Router example (`app/api/v1/metadata.py`)
```python
router = APIRouter(
    prefix="/registry-viewer-api/metadata",
    tags=["metadata-api-controller"],
    dependencies=[Depends(require_scope("read"))],
)

@router.get("/", response_model=MetadataSchema)
async def get_metadata(tag: str = Query(...)):
    ...

@router.put("/", response_model=MetadataSchema,
           dependencies=[Depends(require_scope("write"))])
async def update_metadata(md: MetadataSchema):
    ...
```
- Uses the `require_scope` dependency to enforce `read:metadata` or `write:metadata`.
- Returns Pydantic models (`MetadataSchema`).

## 6. OpenAPI / Swagger integration
- The `OAuth2AuthorizationCodeBearer` scheme is added to the app so the generated OpenAPI spec lists the required scopes per operation.
- Clients can see which scopes are needed directly in Swagger UI.

## 7. Testing strategy
| Test type | Goal |
|-----------|------|
| Unit – OAuth2 | Mock JWKS, sign JWT, verify `oauth.verify_jwt` returns payload & scopes. |
| Unit – Basic‑Auth | Validate correct/incorrect Basic headers and scope extraction. |
| Unit – Permission utility | Test `has_scope` for all actions/registries, including `read:metadata`. |
| Integration – endpoint protection | Use `TestClient` to call `/metadata` with various auth methods and scopes; expect 200, 403, or 401 accordingly. |
| Integration – DB effect | Spin up a temporary PostgreSQL container, run migrations, perform a write request; ensure DB changes only when scope permits. |
| OpenAPI consistency | Fetch `app.openapi()` and assert each operation includes the correct `security` entry with the expected scope. |

## 8. Future registry onboarding
1. Add new SQL scripts to `docs/` and run them against the DB.
2. Generate/hand‑write SQLAlchemy models for the new tables (place in `app/db/models`).
3. Add a new router (or extend existing ones) that uses `{registry}` path param; `require_scope` will automatically enforce `<action>:<new_registry>`.
4. Extend `oauth2_scheme.scopes` with the new `<action>:<new_registry>` entries – FastAPI will propagate them to the docs.

## 9. Documentation updates
- **AGENTS.md** – replace the old “Running the API” block with a description of Auth0 Bearer + Basic‑Auth fallback, scope format, and required env vars.
- **README.md** – add a Configuration section listing env vars, an example `.env`, and curl examples for both auth methods.

## 10. Tasks (ready for a ticket board)
| # | Task | Owner |
|---|------|-------|
| 1 | Add env vars to `.env.example` & docs | – |
| 2 | Implement `app/security/oauth.py` | – |
| 3 | Implement `app/security/basic.py` | – |
| 4 | Implement `app/security/permissions.py` | – |
| 5 | Implement `app/security/deps.py` | – |
| 6 | Add OAuth2 security scheme to `app/main.py` | – |
| 7 | Update routers to use `require_scope` | – |
| 8 | Write unit & integration tests | – |
| 9 | Update `AGENTS.md` with new auth description | – |
|10 | Update `README.md` with configuration & examples | – |
|11 | Verify generated OpenAPI includes scopes | – |
|12 | (Future) Add new registry support as described | – |

---

**This plan can be saved as `PLAN.md` and used as a reference for the implementation phase.**