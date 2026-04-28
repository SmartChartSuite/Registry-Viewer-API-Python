import json
from pathlib import Path

from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure the repository root is on the import path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)

# Load the original spec for comparison
SPEC_PATH = Path(__file__).resolve().parents[1] / "docs" / "api-docs.yaml"
_original_yaml = SPEC_PATH.read_text(encoding="utf-8")
_original_json = None
try:
    import yaml
    _original_json = yaml.safe_load(_original_yaml) or {}
except Exception:
    _original_json = {}

def test_root_returns_yaml():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.oai.openapi")
    # Compare raw content (allow possible trailing newline differences)
    assert response.text.strip() == _original_yaml.strip()

def test_root_returns_json_when_accepted():
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    # Compare JSON structures
    assert response.json() == _original_json

def test_root_not_in_generated_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    # The root path should not be listed in the generated spec
    assert "/" not in data.get("paths", {})
