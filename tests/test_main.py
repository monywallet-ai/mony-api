import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "version" in data

def test_upload_receipt_endpoint_exists():
    """Test that the upload receipt endpoint exists."""
    # This should return 422 (validation error) because no file is provided
    response = client.post("/receipts")
    assert response.status_code == 422  # Validation error expected