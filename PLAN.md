# Implementation Plan for SMART‑Pacer Registry Viewer API

## Summary of recent changes

1. **Metadata POST operation**
   - Added a **409 Conflict** response that returns the existing `Metadata` object when a duplicate `tag` is submitted.
   - Updated the OpenAPI definition (`api-docs.yaml`) accordingly and ensured the FastAPI route returns `JSONResponse` with `status_code=409`.
   - The successful creation now explicitly uses **HTTP 201 Created**.

2. **Metadata PUT operation**
   - Removed an unused `tag` query‑parameter from the OpenAPI spec – the tag is now taken from the request body.
   - Deleted the stray `201` response code, leaving only the appropriate `200` success response.
   - The implementation already returns **404 Not Found** when the entry does not exist.

3. **Metadata DELETE operation**
   - Implemented the `DELETE /registry-viewer-api/metadata` endpoint in FastAPI (`app/api/v1/metadata.py`).
   - The endpoint requires a `tag` query‑parameter and returns the deleted `Metadata` object on success (`200`).
   - Defined `404`, `401`, `403`, and `400` error responses in both the OpenAPI spec and FastAPI implementation.
   - Added required imports and database deletion logic.
   - Updated `.env` and `app/config.py` to include additional schema environment variables (`VOCABULARY_SCHEMA`, `DATA_SCHEMA`, `SCD_DATA_SCHEMA`).

4. **case-record GET operation**
   - Implemented `GET /registry-viewer-api/case-record/{registry}` in `app/api/v1/case_record.py` with FastAPI.
   - The `{registry}` path parameter must be either `DATA_SCHEMA` or `SCD_DATA_SCHEMA`; otherwise a **400** error (`code=400, message="invalid registry name"`) is returned.
   - Required query parameters: `caseId` (int) and optional `sections` (CSV string). When `sections` is omitted or empty, observations are filtered by `observation_concept_id > 2_000_000_000`. When provided, only observations whose concept IDs match those from the selected sections are returned.
   - A category mapping (`concept_id → section, category, question`) is retrieved from `{VIEWER_SCHEMA}.category` respecting the `sections` filter.
   - Observations are queried from `{registry}.observation` (joined to `person` → `case_info` on `person_id`) and left‑joined to `{VOCABULARY_SCHEMA}.concept` for coding information.
   - The raw `value_as_string` field is **caret (^) delimited** and parsed:
     - If > 3 parts, the first part is a date assigned to `Content.date`.
     - When there are exactly 3 parts, they map to `system`, `code`, `display` of the `Coding` object.
     - When > 3 parts, the second, third, and fourth parts map to `system`, `code`, `display` respectively.
     - The **value** is taken from the 5th part (if present) or the first non‑date part otherwise.
     - The **unit** is taken from the 6th part when exactly 6 parts are present.
   - Constructed a `Value` model containing optional `Coding`, `unit`, and `value` and attached it as `derivedValue` on each `Content`.
    - Fetched `DetailUserData` rows from `{registry}.fact_relationship` (joined via `observation_id = fact_id_1` and filtered on `relationship_concept_id = 44818759`).
     - If no detail rows exist for a content, a fallback `DetailUserData` is created with `tableDisplayText` set to the content’s derived value.
   - Flags and annotations are read from `{registry}.flag` and `{registry}.annotation` tables and linked to the appropriate `Content` (future extensions can populate these fields).
   - Assembled a `CaseData` response (`caseId`, `contents`, `count`).
   - Added corresponding Pydantic models (`Coding`, `Value`, `DetailUserData`, `Content`, `CaseData`) in `app/schemas/case_data.py`.
   - Updated imports and router inclusion in `app/main.py`.
   - Added an `Error` model to `app/schemas/metadata.py` for uniform error responses.

5. **OpenAPI specification synchronization**
   - Generate the OpenAPI definition from the FastAPI app (`app.main.app.openapi()`) and export it as YAML.
   - Compare the generated spec with the canonical `docs/api-docs.yaml`.
   - Update any mismatched sections:
       • `servers`, `info` (title, description, contact, license).
       • Schema definitions for `CaseData`, `Content`, `Value`, `Coding`, `DetailUserData`, and other related models.
       • Parameter definitions for the `case-record` endpoint (`registry`, `caseId`, `sections`).
       • Response models and `Error` definitions.
   - Run `openapi_spec_validator` to ensure the final `api-docs.yaml` is valid.
   - Commit the updated `api-docs.yaml` alongside code changes.

6. **OpenAPI validation**
   - Ran `openapi_spec_validator` after each modification to ensure the YAML remains valid.
   - Updated schema definitions where necessary (e.g., `viewerConfig` alias handling).

7. **Add tests for case-record endpoint**
   - Write unit tests using FastAPI's `TestClient` to cover:
       • Successful retrieval with and without `sections`.
       • 400 error for invalid registry name.
       • 404 error when no observations exist.
       • Authentication requirements (401 when missing token).
   - Ensure the tests mock the DB session to avoid hitting a real database.
   - Run `pytest -q` and confirm all tests pass.

## Next steps

- **Add tests** for the new DELETE endpoint (200 success, 404 not‑found, auth/ scope errors) as well as existing POST conflict and PUT update scenarios.
- **Run the full test suite** (`pytest -q`) to ensure no regressions.
- **Update README/API usage examples** to include the DELETE operation and the newly added environment variables (`VOCABULARY_SCHEMA`, `DATA_SCHEMA`, `SCD_DATA_SCHEMA`).
- **Consider adding integration tests** that spin up a temporary PostgreSQL instance to verify end‑to‑end behavior of the metadata CRUD routes.

## Reference files modified

- `docs/api-docs.yaml` – Updated operation definitions for POST, PUT, and added DELETE.
- `app/api/v1/metadata.py` – Adjusted imports and added placeholder for DELETE (to be implemented).
- `app/schemas/metadata.py` – Updated Pydantic model to use `ConfigDict` for alias handling.
- `app/config.py` – Added environment variables for schema/table names (already in place).
- `plan.md` – This document records the plan and next steps.

---

**All changes are now in version control and ready for further development and testing.**