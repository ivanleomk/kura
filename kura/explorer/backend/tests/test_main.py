"""Tests for main FastAPI app endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["explorer_initialized"] is True
        assert "checkpoint_dir" in data
    
    def test_health_check_no_explorer(self):
        """Test health check when explorer is not initialized."""
        with patch('main.explorer', None):
            client = TestClient()
            from main import app
            client = TestClient(app)
            
            response = client.get("/api/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["explorer_initialized"] is False


class TestStatsEndpoint:
    """Test stats endpoint."""
    
    def test_get_stats_success(self, client, mock_explorer):
        """Test successful stats retrieval."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        expected_stats = mock_explorer.get_stats.return_value
        
        assert data["total_conversations"] == expected_stats["total_conversations"]
        assert data["total_messages"] == expected_stats["total_messages"]
        assert data["total_summaries"] == expected_stats["total_summaries"]
        assert data["total_clusters"] == expected_stats["total_clusters"]
        assert data["root_clusters"] == expected_stats["root_clusters"]
        assert data["max_cluster_level"] == expected_stats["max_cluster_level"]
        
        mock_explorer.get_stats.assert_called_once()
    
    def test_get_stats_explorer_not_initialized(self):
        """Test stats endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            client = TestClient(app)
            
            response = client.get("/api/stats")
            assert response.status_code == 503
            assert response.json()["detail"] == "Explorer not initialized"


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = client.options("/api/health")
        assert response.status_code == 200
        
        # Check for CORS headers (these may vary based on client origin)
        headers = response.headers
        assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers


class TestAppConfiguration:
    """Test FastAPI app configuration."""
    
    def test_app_metadata(self):
        """Test app title, description, and version."""
        from main import app
        
        assert app.title == "Kura Explorer API"
        assert app.description == "API for exploring Kura checkpoint data"
        assert app.version == "1.0.0"
    
    def test_router_inclusion(self):
        """Test that all routers are properly included."""
        from main import app
        
        # Check that routes exist for all expected prefixes
        routes = [route.path for route in app.routes]
        
        # Health and stats endpoints
        assert "/api/health" in routes
        assert "/api/stats" in routes
        
        # Router prefixes should be present in some form
        router_patterns = ["/api/clusters", "/api/conversations", "/api/insights", "/api/search"]
        
        for pattern in router_patterns:
            # Check if any route starts with the pattern
            assert any(route.startswith(pattern) for route in routes), f"No routes found for {pattern}"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_404_endpoint(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test that wrong HTTP methods return 405."""
        response = client.post("/api/health")
        assert response.status_code == 405
    
    def test_invalid_json_response_format(self, client):
        """Test that endpoints return valid JSON."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # Should not raise an exception
        data = response.json()
        assert isinstance(data, dict) 