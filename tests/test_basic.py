"""
Basic tests for Sims Thing API
Tests that don't require database setup
"""

import pytest
import json
import os
from app import create_app

# Set test environment variables before importing database modules
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/sims_mud_db_test"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

def test_home_endpoint():
    """Test the home endpoint without database setup."""
    app = create_app()
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

def test_health_endpoint():
    """Test the health endpoint."""
    app = create_app()
    
    with app.test_client() as client:
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert data["status"] == "healthy"

def test_invalid_endpoint():
    """Test that invalid endpoints return 404."""
    app = create_app()
    
    with app.test_client() as client:
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

def test_sims_endpoint_structure():
    """Test the sims endpoint structure (may fail if no database, but should return proper error)."""
    app = create_app()
    
    with app.test_client() as client:
        response = client.get('/api/v1/sims')
        # Should either return 200 with sims data or 500 with error
        assert response.status_code in [200, 500]
        
        if response.status_code == 500:
            data = json.loads(response.data)
            assert "error" in data
        else:
            data = json.loads(response.data)
            assert "sims" in data
