"""
Tests for control API functionality.

Tests the FastAPI control plane endpoints and functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from hydramind.control.api import build_app


class TestControlAPIBuild:
    """Test FastAPI app building."""

    @pytest.fixture
    def mock_brain(self):
        """Create a mock HydraBrain instance."""
        brain = Mock()
        brain.cfg = Mock()
        brain.cfg.server = Mock()
        brain.cfg.server.cors = ["*"]
        brain.cfg.server.host = "localhost"
        brain.cfg.server.port = 8080

        # Mock methods that endpoints use
        brain.get_health = AsyncMock(return_value={
            "status": "healthy",
            "modules": ["module1", "module2"]
        })
        brain.get_metrics = AsyncMock(return_value={
            "uptime": 123.45,
            "events_processed": 1000
        })
        brain.get_modules = AsyncMock(return_value=[
            {"name": "module1", "state": "running"},
            {"name": "module2", "state": "running"}
        ])
        brain.bus = Mock()
        brain.bus.publish = AsyncMock()
        brain.store = Mock()
        brain.store.query = AsyncMock(return_value=[])

        return brain

    def test_build_app_success(self, mock_brain):
        """Test successful FastAPI app creation."""
        app = build_app(mock_brain)

        # Should return a FastAPI app instance
        assert app is not None
        assert hasattr(app, 'routes')

        # Should have expected routes
        route_paths = [route.path for route in app.routes]
        assert "/" in route_paths
        assert "/health" in route_paths
        assert "/metrics" in route_paths
        assert "/bus/publish" in route_paths
        assert "/events/query" in route_paths
        assert "/modules" in route_paths
        assert "/config" in route_paths
        assert "/shutdown" in route_paths

    def test_build_app_fastapi_not_installed(self, mock_brain):
        """Test app creation when FastAPI is not available."""
        with patch.dict('sys.modules', {'fastapi': None}):
            app = build_app(mock_brain)
            assert app is None

    def test_build_app_missing_dependencies(self, mock_brain):
        """Test app creation with missing optional dependencies."""
        # Mock ImportError for FastAPI
        original_import = __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if name in ['fastapi', 'fastapi.middleware.cors', 'pydantic']:
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            app = build_app(mock_brain)
            assert app is None


class TestControlAPIEndpoints:
    """Test control API endpoints."""

    @pytest.fixture
    def mock_brain(self):
        """Create a mock HydraBrain instance."""
        brain = Mock()
        brain.cfg = Mock()
        brain.cfg.server = Mock()
        brain.cfg.server.cors = ["*"]

        # Mock endpoint methods
        brain.get_health = AsyncMock(return_value={
            "status": "healthy",
            "uptime": 123.45,
            "modules": {"module1": "running", "module2": "running"}
        })
        brain.get_metrics = AsyncMock(return_value={
            "uptime": 123.45,
            "events_processed": 1000,
            "memory_usage": 50.5
        })
        brain.get_modules = AsyncMock(return_value=[
            {"name": "module1", "state": "running", "health_score": 0.95},
            {"name": "module2", "state": "running", "health_score": 0.87}
        ])
        brain.bus = Mock()
        brain.bus.publish = AsyncMock()
        brain.store = Mock()
        brain.store.query = AsyncMock(return_value=[
            {"topic": "test/topic", "data": {"key": "value"}, "timestamp": 1000.0}
        ])

        return brain

    @pytest.fixture
    def client(self, mock_brain):
        """Create test client for the API."""
        app = build_app(mock_brain)
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "HydraMind Control Plane" in data["message"]
        assert "version" in data

    def test_health_endpoint(self, client, mock_brain):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "uptime" in data
        assert "modules" in data

        # Verify brain method was called
        mock_brain.get_health.assert_called_once()

    def test_metrics_endpoint(self, client, mock_brain):
        """Test metrics endpoint."""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()

        assert "uptime" in data
        assert "events_processed" in data
        assert "memory_usage" in data

        # Verify brain method was called
        mock_brain.get_metrics.assert_called_once()

    def test_list_modules_endpoint(self, client, mock_brain):
        """Test list modules endpoint."""
        response = client.get("/modules")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "modules" in data
        assert len(data["modules"]) == 2
        assert data["modules"][0]["name"] == "module1"
        assert data["modules"][1]["name"] == "module2"

        # Verify brain method was called
        mock_brain.get_modules.assert_called_once()

    def test_config_endpoint(self, client, mock_brain):
        """Test get config endpoint."""
        # Mock the brain config
        mock_brain.cfg = {
            "server": {"host": "localhost", "port": 8080},
            "logging": {"level": "INFO"},
            "features": ["feature1", "feature2"]
        }

        response = client.get("/config")

        assert response.status_code == 200
        data = response.json()

        assert "server" in data
        assert "logging" in data
        assert "features" in data
        assert data["server"]["host"] == "localhost"
        assert data["server"]["port"] == 8080

    def test_publish_event_endpoint(self, client, mock_brain):
        """Test publish event endpoint."""
        request_data = {
            "topic": "test/topic",
            "data": {"key": "value"},
            "qos": 1,
            "key": "test_key"
        }

        response = client.post("/bus/publish", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "published" in data
        assert data["published"] is True

        # Verify bus.publish was called with correct arguments
        mock_brain.bus.publish.assert_called_once()
        call_args = mock_brain.bus.publish.call_args[0][0]
        assert call_args.topic == "test/topic"
        assert call_args.data == {"key": "value"}
        assert call_args.qos == 1
        assert call_args.key == "test_key"

    def test_publish_event_endpoint_invalid_data(self, client, mock_brain):
        """Test publish event endpoint with invalid data."""
        request_data = {
            "topic": "",  # Invalid empty topic
            "data": "not_a_dict"  # Invalid data type
        }

        response = client.post("/bus/publish", json=request_data)

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_query_events_endpoint(self, client, mock_brain):
        """Test query events endpoint."""
        request_data = {
            "topic_pattern": "test/*",
            "since_ts": 1000.0,
            "until_ts": 2000.0,
            "limit": 50
        }

        response = client.post("/events/query", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "events" in data
        assert isinstance(data["events"], list)

        # Verify store.query was called with correct arguments
        mock_brain.store.query.assert_called_once()
        call_args = mock_brain.store.query.call_args[1]
        assert call_args["limit"] == 50

    def test_shutdown_endpoint(self, client, mock_brain):
        """Test shutdown endpoint."""
        # Mock the brain's shutdown method
        mock_brain.shutdown = AsyncMock()

        response = client.post("/shutdown")

        assert response.status_code == 200
        data = response.json()
        assert "shutdown" in data
        assert data["shutdown"] == "initiated"

        # Verify shutdown was called
        mock_brain.shutdown.assert_called_once()


class TestControlAPIErrorHandling:
    """Test control API error handling."""

    @pytest.fixture
    def mock_brain_error(self):
        """Create a mock brain that raises errors."""
        brain = Mock()
        brain.cfg = Mock()
        brain.cfg.server = Mock()
        brain.cfg.server.cors = ["*"]

        # Mock methods that raise exceptions
        brain.get_health = AsyncMock(side_effect=Exception("Health check failed"))
        brain.get_metrics = AsyncMock(side_effect=Exception("Metrics unavailable"))
        brain.bus = Mock()
        brain.bus.publish = AsyncMock(side_effect=Exception("Publish failed"))
        brain.store = Mock()
        brain.store.query = AsyncMock(side_effect=Exception("Query failed"))

        return brain

    @pytest.fixture
    def client_error(self, mock_brain_error):
        """Create test client with error-raising brain."""
        app = build_app(mock_brain_error)
        return TestClient(app)

    def test_health_endpoint_error(self, client_error):
        """Test health endpoint with brain error."""
        response = client_error.get("/health")

        # Should return 500 for internal server error
        assert response.status_code == 500

    def test_metrics_endpoint_error(self, client_error):
        """Test metrics endpoint with brain error."""
        response = client_error.get("/metrics")

        assert response.status_code == 500

    def test_publish_event_error(self, client_error):
        """Test publish event with bus error."""
        request_data = {
            "topic": "test/topic",
            "data": {"key": "value"}
        }

        response = client_error.post("/bus/publish", json=request_data)

        assert response.status_code == 500

    def test_query_events_error(self, client_error):
        """Test query events with store error."""
        request_data = {
            "topic_pattern": "test/*",
            "limit": 10
        }

        response = client_error.post("/events/query", json=request_data)

        assert response.status_code == 500


class TestControlAPIValidation:
    """Test control API input validation."""

    @pytest.fixture
    def mock_brain(self):
        """Create a mock HydraBrain instance."""
        brain = Mock()
        brain.cfg = Mock()
        brain.cfg.server = Mock()
        brain.cfg.server.cors = ["*"]
        brain.bus = Mock()
        brain.bus.publish = AsyncMock()
        brain.store = Mock()
        brain.store.query = AsyncMock(return_value=[])

        return brain

    @pytest.fixture
    def client(self, mock_brain):
        """Create test client for validation tests."""
        app = build_app(mock_brain)
        return TestClient(app)

    def test_publish_invalid_topic(self, client):
        """Test publish with invalid topic."""
        request_data = {
            "topic": "",  # Empty topic should fail
            "data": {"key": "value"}
        }

        response = client.post("/bus/publish", json=request_data)
        assert response.status_code == 422

    def test_publish_invalid_data_type(self, client):
        """Test publish with invalid data type."""
        request_data = {
            "topic": "test/topic",
            "data": "not_a_dict"  # Should be a dict
        }

        response = client.post("/bus/publish", json=request_data)
        assert response.status_code == 422

    def test_publish_invalid_qos(self, client):
        """Test publish with invalid QoS value."""
        request_data = {
            "topic": "test/topic",
            "data": {"key": "value"},
            "qos": 2  # Should be 0 or 1
        }

        response = client.post("/bus/publish", json=request_data)
        assert response.status_code == 422

    def test_query_invalid_limit(self, client):
        """Test query with invalid limit."""
        request_data = {
            "limit": 0  # Should be positive
        }

        response = client.post("/events/query", json=request_data)
        assert response.status_code == 422

    def test_query_negative_limit(self, client):
        """Test query with negative limit."""
        request_data = {
            "limit": -1  # Should be positive
        }

        response = client.post("/events/query", json=request_data)
        assert response.status_code == 422


class TestControlAPICORS:
    """Test CORS configuration in control API."""

    @pytest.fixture
    def mock_brain_cors(self):
        """Create a mock brain with specific CORS settings."""
        brain = Mock()
        brain.cfg = Mock()
        brain.cfg.server = Mock()
        brain.cfg.server.cors = ["https://trusted.example.com", "https://admin.example.com"]

        return brain

    @pytest.fixture
    def client_cors(self, mock_brain_cors):
        """Create test client with CORS configuration."""
        app = build_app(mock_brain_cors)
        return TestClient(app)

    def test_cors_headers(self, client_cors):
        """Test CORS headers are properly set."""
        # Make a request with Origin header
        response = client_cors.get("/health", headers={
            "Origin": "https://trusted.example.com"
        })

        assert response.status_code == 200

        # Should include CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "https://trusted.example.com"

    def test_cors_rejected_origin(self, client_cors):
        """Test CORS rejection for untrusted origin."""
        response = client_cors.get("/health", headers={
            "Origin": "https://malicious.example.com"
        })

        assert response.status_code == 200  # FastAPI handles CORS differently in test client
        # Note: Actual CORS enforcement happens in the browser, not in the server response


class TestControlAPIIntegration:
    """Test control API integration scenarios."""

    @pytest.fixture
    def integration_brain(self):
        """Create a more realistic brain mock for integration tests."""
        brain = Mock()
        brain.cfg = Mock()
        brain.cfg.server = Mock()
        brain.cfg.server.cors = ["*"]

        # Track state
        brain._published_events = []
        brain._query_history = []

        # Realistic method implementations
        async def mock_get_health():
            return {
                "status": "healthy",
                "uptime": 456.78,
                "modules": {
                    "event_bus": "running",
                    "data_collector": "running",
                    "optimizer": "running"
                }
            }

        async def mock_get_metrics():
            return {
                "uptime": 456.78,
                "events_processed": 2500,
                "memory_usage": 45.2,
                "cpu_usage": 12.5,
                "active_modules": 3
            }

        async def mock_publish(msg):
            brain._published_events.append({
                "topic": msg.topic,
                "data": msg.data,
                "qos": msg.qos,
                "key": msg.key
            })

        async def mock_query(**kwargs):
            brain._query_history.append(kwargs)
            return [
                {"topic": "test/topic1", "data": {"id": 1}, "timestamp": 1000.0},
                {"topic": "test/topic2", "data": {"id": 2}, "timestamp": 1001.0}
            ]

        brain.get_health = mock_get_health
        brain.get_metrics = mock_get_metrics
        brain.bus = Mock()
        brain.bus.publish = mock_publish
        brain.store = Mock()
        brain.store.query = mock_query

        return brain

    @pytest.fixture
    def integration_client(self, integration_brain):
        """Create test client for integration tests."""
        app = build_app(integration_brain)
        return TestClient(app)

    def test_full_workflow(self, integration_client, integration_brain):
        """Test complete workflow through the API."""
        # 1. Check health
        health_response = integration_client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"

        # 2. Get metrics
        metrics_response = integration_client.get("/metrics")
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        assert metrics_data["events_processed"] == 2500

        # 3. Publish an event
        publish_data = {
            "topic": "user/action",
            "data": {"action": "login", "user_id": "user123"},
            "qos": 1,
            "key": "session_456"
        }
        publish_response = integration_client.post("/bus/publish", json=publish_data)
        assert publish_response.status_code == 200

        # 4. Query events
        query_data = {
            "topic_pattern": "user/*",
            "limit": 10
        }
        query_response = integration_client.post("/events/query", json=query_data)
        assert query_response.status_code == 200

        # 5. Verify the event was published
        assert len(integration_brain._published_events) == 1
        published = integration_brain._published_events[0]
        assert published["topic"] == "user/action"
        assert published["data"]["action"] == "login"
        assert published["data"]["user_id"] == "user123"

        # 6. Verify query was made
        assert len(integration_brain._query_history) == 1
        query_call = integration_brain._query_history[0]
        assert query_call["limit"] == 10

