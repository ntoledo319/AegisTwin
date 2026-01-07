"""
API Endpoint Integration Tests

Tests for all REST API endpoints.

@ai_prompt: Run with pytest tests/integration/test_api_endpoints.py -v
@context_boundary: tests/integration/test_api_endpoints

# AI-GENERATED 2026-01-07
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health and info endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test GET /health."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test GET /."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "AegisTwin"


class TestIngestEndpoint:
    """Tests for POST /ingest."""
    
    def test_ingest_success(self, client: TestClient):
        """Test successful ingestion."""
        response = client.post("/ingest", json={
            "data": {"records": [{"id": 1}]},
            "source": "test",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "run_id" in data
    
    def test_ingest_empty_data(self, client: TestClient):
        """Test ingestion with empty data."""
        response = client.post("/ingest", json={
            "data": {},
            "source": "test",
        })
        
        assert response.status_code == 200
    
    def test_ingest_invalid_body(self, client: TestClient):
        """Test ingestion with invalid body."""
        response = client.post("/ingest", json={
            "invalid": "body",
        })
        
        assert response.status_code == 422  # Validation error


class TestQueryEndpoint:
    """Tests for POST /query."""
    
    def test_query_success(self, client: TestClient):
        """Test successful query."""
        response = client.post("/query", json={
            "query": "What is the latest data?",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "result" in data
    
    def test_query_with_context(self, client: TestClient):
        """Test query with context."""
        response = client.post("/query", json={
            "query": "Find emails from today",
            "context": {"date": "2026-01-07"},
        })
        
        assert response.status_code == 200


class TestDemoEndpoints:
    """Tests for demo endpoints."""
    
    def test_demo_pipeline(self, client: TestClient):
        """Test POST /demo/pipeline."""
        response = client.post("/demo/pipeline")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_demo_invalid(self, client: TestClient):
        """Test invalid demo name."""
        response = client.post("/demo/invalid_demo")
        
        assert response.status_code in [400, 500]


class TestPoliciesEndpoint:
    """Tests for GET /policies."""
    
    def test_list_policies(self, client: TestClient):
        """Test listing policies."""
        response = client.get("/policies")
        
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert isinstance(data["policies"], list)
    
    def test_policies_structure(self, client: TestClient):
        """Test policy structure."""
        response = client.get("/policies")
        data = response.json()
        
        if data["policies"]:
            policy = data["policies"][0]
            assert "id" in policy
            assert "action" in policy
            assert "effect" in policy


class TestMetricsEndpoint:
    """Tests for GET /metrics."""
    
    def test_metrics_endpoint(self, client: TestClient):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        # Should be plain text
        assert "aegistwin" in response.text.lower() or response.text.startswith("#")


class TestWebSocketInfo:
    """Tests for WebSocket info endpoint."""
    
    def test_ws_info(self, client: TestClient):
        """Test GET /ws/info."""
        response = client.get("/ws/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_connections" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
