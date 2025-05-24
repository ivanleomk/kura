"""Tests for clusters router."""

from unittest.mock import Mock, patch


class TestGetClusters:
    """Test GET /api/clusters endpoint."""

    def test_get_clusters_success(self, client, mock_explorer):
        """Test successful clusters retrieval."""
        response = client.get("/api/clusters")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        assert len(data["items"]) > 0
        cluster = data["items"][0]
        assert "id" in cluster
        assert "name" in cluster
        assert "description" in cluster
        assert "level" in cluster
        assert "conversation_count" in cluster

    def test_get_clusters_with_pagination(self, client):
        """Test clusters with pagination parameters."""
        response = client.get("/api/clusters?limit=10&offset=5")
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5

    def test_get_clusters_with_filtering(self, client):
        """Test clusters with various filters."""
        # Test parent_id filter
        response = client.get("/api/clusters?parent_id=cluster_1")
        assert response.status_code == 200

        # Test level filter
        response = client.get("/api/clusters?level=0")
        assert response.status_code == 200

        # Test language filter
        response = client.get("/api/clusters?language=python")
        assert response.status_code == 200

        # Test frustration filter
        response = client.get("/api/clusters?min_frustration=2")
        assert response.status_code == 200

    def test_get_clusters_with_sorting(self, client):
        """Test clusters with different sorting options."""
        # Test sort by name
        response = client.get("/api/clusters?sort_by=name&sort_desc=true")
        assert response.status_code == 200

        # Test sort by conversation count
        response = client.get("/api/clusters?sort_by=conversation_count")
        assert response.status_code == 200

        # Test sort by frustration
        response = client.get("/api/clusters?sort_by=frustration")
        assert response.status_code == 200

    def test_get_clusters_invalid_sort_param(self, client):
        """Test clusters with invalid sort parameter."""
        response = client.get("/api/clusters?sort_by=invalid_field")
        assert response.status_code == 422  # Validation error

    def test_get_clusters_invalid_pagination(self, client):
        """Test clusters with invalid pagination parameters."""
        # Negative offset
        response = client.get("/api/clusters?offset=-1")
        assert response.status_code == 422

        # Invalid limit
        response = client.get("/api/clusters?limit=0")
        assert response.status_code == 422

        # Limit too large
        response = client.get("/api/clusters?limit=300")
        assert response.status_code == 422

    def test_get_clusters_explorer_not_initialized(self):
        """Test clusters endpoint when explorer is not initialized."""
        with patch("main.explorer", None):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            response = client.get("/api/clusters")
            assert response.status_code == 503
            assert response.json()["detail"] == "Explorer not initialized"


class TestGetClusterTree:
    """Test GET /api/clusters/tree endpoint."""

    def test_get_cluster_tree_success(self, client, mock_explorer):
        """Test successful cluster tree retrieval."""
        response = client.get("/api/clusters/tree")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            node = data[0]
            assert "id" in node
            assert "name" in node
            assert "description" in node
            assert "level" in node
            assert "conversation_count" in node
            assert "children" in node
            assert isinstance(node["children"], list)

    def test_get_cluster_tree_explorer_not_initialized(self):
        """Test cluster tree endpoint when explorer is not initialized."""
        with patch("main.explorer", None):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            response = client.get("/api/clusters/tree")
            assert response.status_code == 503


class TestGetCluster:
    """Test GET /api/clusters/{cluster_id} endpoint."""

    def test_get_cluster_success(self, client, mock_explorer):
        """Test successful single cluster retrieval."""
        response = client.get("/api/clusters/cluster_1")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "cluster_1"
        assert "name" in data
        assert "description" in data
        assert "level" in data
        assert "conversation_count" in data
        assert "children" in data
        assert "sample_conversations" in data
        assert "hierarchy" in data

        # Check children structure
        assert isinstance(data["children"], list)

        # Check sample conversations structure
        assert isinstance(data["sample_conversations"], list)
        if len(data["sample_conversations"]) > 0:
            conv = data["sample_conversations"][0]
            assert "id" in conv
            assert "created_at" in conv
            assert "metadata" in conv
            assert "message_count" in conv

    def test_get_cluster_not_found(self, client, mock_explorer):
        """Test cluster not found."""
        # Mock explorer to return None for non-existent cluster
        mock_explorer.get_cluster.return_value = None

        response = client.get("/api/clusters/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Cluster not found"

    def test_get_cluster_explorer_not_initialized(self):
        """Test single cluster endpoint when explorer is not initialized."""
        with patch("main.explorer", None):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            response = client.get("/api/clusters/cluster_1")
            assert response.status_code == 503


class TestGetClusterSummary:
    """Test GET /api/clusters/{cluster_id}/summary endpoint."""

    def test_get_cluster_summary_success(self, client, mock_explorer):
        """Test successful cluster summary retrieval."""
        # Mock the cluster and database session
        cluster_mock = Mock()
        cluster_mock.name = "Python Development"
        mock_explorer.get_cluster.return_value = cluster_mock

        with patch("routers.clusters.Session") as mock_session:
            # Mock database session and query results
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            # Mock summaries data
            summary_mock = Mock()
            summary_mock.languages = ["python"]
            summary_mock.user_frustration = 2
            summary_mock.task = "data_analysis"
            summary_mock.summary = "User asked about pandas"

            mock_session_instance.exec.return_value.all.return_value = [
                summary_mock
            ] * 5

            response = client.get("/api/clusters/cluster_1/summary")
            assert response.status_code == 200

            data = response.json()
            assert data["cluster_id"] == "cluster_1"
            assert data["cluster_name"] == "Python Development"
            assert "total_conversations" in data
            assert "language_distribution" in data
            assert "frustration_distribution" in data
            assert "top_tasks" in data
            assert "sample_summaries" in data

    def test_get_cluster_summary_not_found(self, client, mock_explorer):
        """Test cluster summary for non-existent cluster."""
        mock_explorer.get_cluster.return_value = None

        response = client.get("/api/clusters/nonexistent/summary")
        assert response.status_code == 404
        assert response.json()["detail"] == "Cluster not found"

    def test_get_cluster_summary_explorer_not_initialized(self):
        """Test cluster summary endpoint when explorer is not initialized."""
        with patch("main.explorer", None):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            response = client.get("/api/clusters/cluster_1/summary")
            assert response.status_code == 503


class TestClusterResponseModels:
    """Test cluster response model validation."""

    def test_cluster_response_required_fields(self, client):
        """Test that cluster responses have all required fields."""
        response = client.get("/api/clusters")
        assert response.status_code == 200

        data = response.json()
        if len(data["items"]) > 0:
            cluster = data["items"][0]

            # Required fields
            required_fields = [
                "id",
                "name",
                "description",
                "level",
                "conversation_count",
            ]
            for field in required_fields:
                assert field in cluster, f"Missing required field: {field}"

    def test_cluster_detail_response_structure(self, client):
        """Test cluster detail response structure."""
        response = client.get("/api/clusters/cluster_1")
        assert response.status_code == 200

        data = response.json()

        # Check nested structures
        assert isinstance(data.get("children", []), list)
        assert isinstance(data.get("sample_conversations", []), list)
        assert isinstance(data.get("hierarchy", []), list)

        # Parent can be null or object
        parent = data.get("parent")
        if parent is not None:
            assert isinstance(parent, dict)
            assert "id" in parent
            assert "name" in parent


class TestClusterDependencyInjection:
    """Test dependency injection for explorer."""

    def test_get_explorer_dependency_success(self, client, mock_explorer):
        """Test that explorer dependency is properly injected."""
        response = client.get("/api/clusters")
        assert response.status_code == 200

        # Verify that the mock explorer methods were called
        mock_explorer.get_clusters.assert_called()

    def test_get_explorer_dependency_failure(self):
        """Test explorer dependency when import fails."""
        with patch("main.explorer", None):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            response = client.get("/api/clusters")
            assert response.status_code == 503
            assert "Explorer not initialized" in response.json()["detail"]
