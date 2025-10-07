import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_search_candidates_success():
    """Test successful candidate search."""
    response = client.post("/api/v1/candidates/search", json={})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "pagination" in data

def test_get_filter_options_success():
    """Test successful retrieval of filter options."""
    response = client.get("/api/v1/candidates/filter-options")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert "locations" in data

def test_create_and_get_filter_presets():
    """Test creating and retrieving a filter preset."""
    preset_data = {
        "name": "Test Preset",
        "filters": {"skills": ["Python"]}
    }
    create_response = client.post("/api/v1/candidates/filter-presets", json=preset_data)
    assert create_response.status_code == 200
    created_preset = create_response.json()
    assert created_preset["name"] == "Test Preset"

    get_response = client.get("/api/v1/candidates/filter-presets")
    assert get_response.status_code == 200
    presets = get_response.json()
    assert len(presets) > 0
    assert presets[0]["name"] == "Test Preset"
