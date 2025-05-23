"""Tests for insights router."""

import pytest
from unittest.mock import Mock, patch


class TestLanguageStatistics:
    """Test GET /api/insights/language-stats endpoint."""
    
    def test_get_language_statistics_success(self, client, mock_explorer):
        """Test successful language statistics retrieval."""
        # Mock database session and summaries
        with patch('routers.insights.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            # Mock summaries with languages
            summaries = [
                Mock(languages=["python", "javascript"]),
                Mock(languages=["python"]),
                Mock(languages=["java"]),
                Mock(languages=["python", "sql"]),
                Mock(languages=None)  # No languages
            ]
            mock_session_instance.exec.return_value.all.return_value = summaries
            
            response = client.get("/api/insights/language-stats")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            
            if len(data) > 0:
                stat = data[0]
                assert "language" in stat
                assert "count" in stat
                assert "percentage" in stat
                assert isinstance(stat["count"], int)
                assert isinstance(stat["percentage"], float)
    
    def test_get_language_statistics_empty_data(self, client, mock_explorer):
        """Test language statistics with no data."""
        with patch('routers.insights.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.return_value = []
            
            response = client.get("/api/insights/language-stats")
            assert response.status_code == 200
            assert response.json() == []
    
    def test_get_language_statistics_explorer_not_initialized(self):
        """Test language stats endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/insights/language-stats")
            assert response.status_code == 503


class TestFrustrationHeatmap:
    """Test GET /api/insights/frustration-map endpoint."""
    
    def test_get_frustration_heatmap_success(self, client, mock_explorer):
        """Test successful frustration heatmap retrieval."""
        with patch('routers.insights.Session') as mock_session:
            # Mock clusters
            clusters = [
                Mock(id="cluster1", name="Python Development", x_coord=0.5, y_coord=0.3),
                Mock(id="cluster2", name="Web Development", x_coord=0.7, y_coord=0.6)
            ]
            
            # Mock summaries with frustration scores
            summaries = [
                Mock(user_frustration=3),
                Mock(user_frustration=4),
                Mock(user_frustration=2),
                Mock(user_frustration=5),
                Mock(user_frustration=3),
                Mock(user_frustration=None)  # No frustration
            ]
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.side_effect = [clusters, summaries, summaries]
            
            response = client.get("/api/insights/frustration-map")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            
            if len(data) > 0:
                item = data[0]
                assert "cluster_id" in item
                assert "cluster_name" in item
                assert "avg_frustration" in item
                assert "conversation_count" in item
                assert "x_coord" in item
                assert "y_coord" in item
    
    def test_get_frustration_heatmap_with_min_conversations(self, client, mock_explorer):
        """Test frustration heatmap with minimum conversations filter."""
        with patch('routers.insights.Session') as mock_session:
            clusters = [Mock(id="cluster1", name="Small Cluster")]
            summaries = [Mock(user_frustration=3)]  # Only 1 conversation
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.side_effect = [clusters, summaries]
            
            response = client.get("/api/insights/frustration-map?min_conversations=5")
            assert response.status_code == 200
            
            # Should filter out clusters with < 5 conversations
            data = response.json()
            assert len(data) == 0  # Cluster filtered out
    
    def test_get_frustration_heatmap_explorer_not_initialized(self):
        """Test frustration heatmap endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/insights/frustration-map")
            assert response.status_code == 503


class TestMetadataDistribution:
    """Test GET /api/insights/metadata-dist endpoint."""
    
    def test_get_metadata_distribution_success(self, client, mock_explorer):
        """Test successful metadata distribution retrieval."""
        with patch('routers.insights.Session') as mock_session:
            # Mock conversations with metadata
            conversations = [
                Mock(metadata_json={"source": "web"}),
                Mock(metadata_json={"source": "api"}),
                Mock(metadata_json={"source": "web"}),
                Mock(metadata_json={"source": "mobile"}),
                Mock(metadata_json={"other_key": "value"}),  # Different key
                Mock(metadata_json=None)  # No metadata
            ]
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.return_value = conversations
            
            response = client.get("/api/insights/metadata-dist?key=source")
            assert response.status_code == 200
            
            data = response.json()
            assert data["key"] == "source"
            assert data["total_conversations"] == 6
            assert data["conversations_with_key"] == 4
            assert "value_distribution" in data
            assert "unique_values" in data
            assert isinstance(data["value_distribution"], dict)
    
    def test_get_metadata_distribution_missing_key(self, client):
        """Test metadata distribution without key parameter."""
        response = client.get("/api/insights/metadata-dist")
        assert response.status_code == 422  # Validation error
    
    def test_get_metadata_distribution_explorer_not_initialized(self):
        """Test metadata distribution endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/insights/metadata-dist?key=source")
            assert response.status_code == 503


class TestCommonThemes:
    """Test GET /api/insights/themes endpoint."""
    
    def test_get_common_themes_success(self, client, mock_explorer):
        """Test successful common themes retrieval."""
        with patch('routers.insights.Session') as mock_session:
            # Mock clusters with theme-related names
            clusters = [
                Mock(id="c1", name="Python Programming"),
                Mock(id="c2", name="Python Data Science"),
                Mock(id="c3", name="Web Development"),
                Mock(id="c4", name="Javascript Frontend"),
                Mock(id="c5", name="Database Queries")
            ]
            
            # Mock summaries
            summaries = [
                Mock(summary="How to use pandas"),
                Mock(summary="Python basics")
            ]
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.side_effect = [clusters, summaries, summaries, summaries]
            
            response = client.get("/api/insights/themes")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            
            if len(data) > 0:
                theme = data[0]
                assert "theme" in theme
                assert "cluster_ids" in theme
                assert "frequency" in theme
                assert "example_summaries" in theme
                assert isinstance(theme["cluster_ids"], list)
                assert isinstance(theme["example_summaries"], list)
    
    def test_get_common_themes_with_min_frequency(self, client, mock_explorer):
        """Test themes with minimum frequency filter."""
        with patch('routers.insights.Session') as mock_session:
            clusters = [Mock(id="c1", name="Unique Topic")]  # Only 1 cluster
            summaries = []
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.side_effect = [clusters, summaries]
            
            response = client.get("/api/insights/themes?min_frequency=3")
            assert response.status_code == 200
            
            # Should filter out themes with frequency < 3
            data = response.json()
            assert len(data) == 0
    
    def test_get_common_themes_explorer_not_initialized(self):
        """Test themes endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/insights/themes")
            assert response.status_code == 503


class TestOutlierConversations:
    """Test GET /api/insights/outliers endpoint."""
    
    def test_get_outliers_success(self, client, mock_explorer):
        """Test successful outlier conversations retrieval."""
        with patch('routers.insights.Session') as mock_session:
            # Mock different types of outliers
            high_frustration_convs = [Mock(chat_id="conv1", message_count=10)]
            short_convs = [Mock(chat_id="conv2", message_count=1)]
            multilang_summaries = [Mock(chat_id="conv3", languages=["python", "java", "sql"])]
            error_summaries = [Mock(chat_id="conv4", assistant_errors=["syntax_error"])]
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            
            # Mock database queries
            mock_session_instance.exec.return_value.all.side_effect = [
                high_frustration_convs,  # High frustration
                short_convs,             # Short conversations
                multilang_summaries + [Mock(languages=["python"])],  # All summaries
                error_summaries          # Error summaries
            ]
            
            response = client.get("/api/insights/outliers")
            assert response.status_code == 200
            
            data = response.json()
            assert "high_frustration" in data
            assert "very_short" in data
            assert "multilingual" in data
            assert "assistant_errors" in data
            
            assert isinstance(data["high_frustration"], list)
            assert isinstance(data["very_short"], list)
            assert isinstance(data["multilingual"], list)
            assert isinstance(data["assistant_errors"], list)
    
    def test_get_outliers_with_limit(self, client, mock_explorer):
        """Test outliers with custom limit."""
        with patch('routers.insights.Session'):
            response = client.get("/api/insights/outliers?limit=10")
            assert response.status_code == 200
    
    def test_get_outliers_invalid_limit(self, client):
        """Test outliers with invalid limit."""
        response = client.get("/api/insights/outliers?limit=0")
        assert response.status_code == 422
        
        response = client.get("/api/insights/outliers?limit=200")
        assert response.status_code == 422
    
    def test_get_outliers_explorer_not_initialized(self):
        """Test outliers endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/insights/outliers")
            assert response.status_code == 503


class TestCommonPatterns:
    """Test GET /api/insights/common-patterns endpoint."""
    
    def test_get_common_patterns_success(self, client, mock_explorer):
        """Test successful common patterns retrieval."""
        with patch('routers.insights.Session') as mock_session:
            # Mock conversation length distribution
            length_dist = [(10, 50), (5, 30), (15, 20)]  # (message_count, frequency)
            task_counts = [("coding", 40), ("debugging", 25), ("learning", 15)]
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.side_effect = [length_dist, task_counts]
            
            response = client.get("/api/insights/common-patterns")
            assert response.status_code == 200
            
            data = response.json()
            assert "conversation_length_distribution" in data
            assert "common_tasks" in data
            assert "average_conversation_length" in data
            
            assert isinstance(data["conversation_length_distribution"], list)
            assert isinstance(data["common_tasks"], list)
            assert isinstance(data["average_conversation_length"], float)
            
            if len(data["conversation_length_distribution"]) > 0:
                item = data["conversation_length_distribution"][0]
                assert "message_count" in item
                assert "frequency" in item
            
            if len(data["common_tasks"]) > 0:
                task = data["common_tasks"][0]
                assert "task" in task
                assert "frequency" in task
    
    def test_get_common_patterns_explorer_not_initialized(self):
        """Test common patterns endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/insights/common-patterns")
            assert response.status_code == 503


class TestClusterComparison:
    """Test POST /api/insights/compare-clusters endpoint."""
    
    def test_compare_clusters_success(self, client, mock_explorer):
        """Test successful cluster comparison."""
        # Mock clusters
        cluster1 = Mock(
            id="cluster1",
            name="Python Development",
            conversation_count=25,
            level=0
        )
        cluster2 = Mock(
            id="cluster2", 
            name="Web Development",
            conversation_count=30,
            level=0
        )
        
        mock_explorer.get_cluster.side_effect = [cluster1, cluster2]
        
        with patch('routers.insights.Session') as mock_session:
            # Mock summaries for each cluster
            summaries = [
                Mock(user_frustration=3, languages=["python"], task="coding"),
                Mock(user_frustration=4, languages=["python", "sql"], task="debugging")
            ]
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.return_value = summaries
            
            response = client.post("/api/insights/compare-clusters", 
                                 json=["cluster1", "cluster2"])
            assert response.status_code == 200
            
            data = response.json()
            assert "clusters" in data
            assert len(data["clusters"]) == 2
            
            for cluster_data in data["clusters"]:
                assert "cluster_id" in cluster_data
                assert "cluster_name" in cluster_data
                assert "conversation_count" in cluster_data
                assert "avg_frustration" in cluster_data
                assert "top_languages" in cluster_data
                assert "top_tasks" in cluster_data
                assert "level" in cluster_data
    
    def test_compare_clusters_invalid_count(self, client):
        """Test cluster comparison with invalid number of clusters."""
        # Too few clusters
        response = client.post("/api/insights/compare-clusters", json=["cluster1"])
        assert response.status_code == 400
        assert "Please provide 2-5 cluster IDs" in response.json()["detail"]
        
        # Too many clusters
        response = client.post("/api/insights/compare-clusters", 
                             json=["c1", "c2", "c3", "c4", "c5", "c6"])
        assert response.status_code == 400
    
    def test_compare_clusters_nonexistent_cluster(self, client, mock_explorer):
        """Test cluster comparison with non-existent cluster."""
        mock_explorer.get_cluster.side_effect = [None, None]  # Both clusters not found
        
        response = client.post("/api/insights/compare-clusters", 
                             json=["nonexistent1", "nonexistent2"])
        assert response.status_code == 200
        
        data = response.json()
        assert data["clusters"] == []  # No clusters found
    
    def test_compare_clusters_explorer_not_initialized(self):
        """Test cluster comparison when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.post("/api/insights/compare-clusters", 
                                 json=["cluster1", "cluster2"])
            assert response.status_code == 503


class TestInsightsResponseModels:
    """Test insights response model validation."""
    
    def test_language_stats_response_structure(self, client, mock_explorer):
        """Test language statistics response structure."""
        with patch('routers.insights.Session') as mock_session:
            summaries = [Mock(languages=["python"])]
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.return_value = summaries
            
            response = client.get("/api/insights/language-stats")
            assert response.status_code == 200
            
            data = response.json()
            for stat in data:
                assert isinstance(stat["language"], str)
                assert isinstance(stat["count"], int)
                assert isinstance(stat["percentage"], (int, float))
                assert 0 <= stat["percentage"] <= 100
    
    def test_frustration_map_response_structure(self, client, mock_explorer):
        """Test frustration map response structure."""
        with patch('routers.insights.Session') as mock_session:
            clusters = [Mock(id="c1", name="Test", x_coord=0.5, y_coord=0.3)]
            summaries = [Mock(user_frustration=3)] * 5
            
            mock_session_instance = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_instance
            mock_session_instance.exec.return_value.all.side_effect = [clusters, summaries]
            
            response = client.get("/api/insights/frustration-map")
            assert response.status_code == 200
            
            data = response.json()
            for item in data:
                assert isinstance(item["avg_frustration"], (int, float))
                assert 1 <= item["avg_frustration"] <= 5
                assert isinstance(item["conversation_count"], int)
                assert item["conversation_count"] > 0 