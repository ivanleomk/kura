"""Tests for search router."""

from unittest.mock import Mock, patch


class TestSearchConversations:
    """Test GET /api/search endpoint."""

    def test_search_conversations_success(self, client, mock_explorer):
        """Test successful conversation search."""
        response = client.get("/api/search?q=pandas")
        assert response.status_code == 200

        data = response.json()
        assert "conversations" in data
        assert "total_count" in data
        assert "query" in data
        assert data["query"] == "pandas"

        assert isinstance(data["conversations"], list)
        if len(data["conversations"]) > 0:
            conversation = data["conversations"][0]
            assert "id" in conversation
            assert "created_at" in conversation
            assert "metadata" in conversation
            assert "message_count" in conversation
            assert "cluster_names" in conversation

        # Verify the search method was called
        mock_explorer.search_conversations.assert_called_once_with("pandas")

    def test_search_conversations_with_limit(self, client, mock_explorer):
        """Test search with custom limit."""
        # Mock more results than the limit
        mock_results = [
            Mock(
                chat_id=f"conv_{i}",
                created_at="2024-01-01T00:00:00",
                metadata_json={},
                message_count=10,
                clusters=[],
            )
            for i in range(100)
        ]

        mock_explorer.search_conversations.return_value = mock_results

        response = client.get("/api/search?q=python&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "python"
        assert len(data["conversations"]) <= 10
        # Total count should reflect the actual search results
        assert data["total_count"] == 100

    def test_search_conversations_empty_results(self, client, mock_explorer):
        """Test search with no results."""
        mock_explorer.search_conversations.return_value = []

        response = client.get("/api/search?q=nonexistent")
        assert response.status_code == 200

        data = response.json()
        assert data["conversations"] == []
        assert data["total_count"] == 0
        assert data["query"] == "nonexistent"

    def test_search_conversations_with_summaries(self, client, mock_explorer):
        """Test search results include summaries."""
        # Mock a conversation result
        mock_conv = Mock(
            chat_id="conv1",
            created_at="2024-01-01T00:00:00",
            metadata_json={"source": "web"},
            message_count=10,
            clusters=[Mock(name="Python Development")],
        )
        mock_explorer.search_conversations.return_value = [mock_conv]

        # Mock summary
        mock_summary = Mock(
            chat_id="conv1",
            summary="User asked about pandas",
            languages=["python"],
            task="data_analysis",
            user_frustration=2,
        )
        mock_explorer.get_summary.return_value = mock_summary

        response = client.get("/api/search?q=pandas")
        assert response.status_code == 200

        data = response.json()
        assert len(data["conversations"]) == 1

        conversation = data["conversations"][0]
        assert conversation["id"] == "conv1"
        assert conversation["summary"] is not None
        assert conversation["summary"]["summary"] == "User asked about pandas"
        assert conversation["cluster_names"] == ["Python Development"]

    def test_search_conversations_without_summaries(self, client, mock_explorer):
        """Test search results when conversations have no summaries."""
        # Mock a conversation result
        mock_conv = Mock(
            chat_id="conv1",
            created_at="2024-01-01T00:00:00",
            metadata_json={"source": "web"},
            message_count=10,
            clusters=[],
        )
        mock_explorer.search_conversations.return_value = [mock_conv]

        # Mock no summary
        mock_explorer.get_summary.return_value = None

        response = client.get("/api/search?q=test")
        assert response.status_code == 200

        data = response.json()
        assert len(data["conversations"]) == 1

        conversation = data["conversations"][0]
        assert conversation["summary"] is None
        assert conversation["cluster_names"] == []


class TestSearchValidation:
    """Test search query validation."""

    def test_search_missing_query(self, client):
        """Test search without query parameter."""
        response = client.get("/api/search")
        assert response.status_code == 422  # Validation error

    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/api/search?q=")
        assert response.status_code == 422  # Validation error

    def test_search_query_too_short(self, client):
        """Test search with query that's too short."""
        response = client.get("/api/search?q=a")
        assert response.status_code == 422  # Validation error

    def test_search_valid_minimum_query(self, client):
        """Test search with minimum valid query length."""
        response = client.get("/api/search?q=ab")
        assert response.status_code == 200

    def test_search_invalid_limit(self, client):
        """Test search with invalid limit parameters."""
        # Negative limit
        response = client.get("/api/search?q=test&limit=0")
        assert response.status_code == 422

        # Limit too large
        response = client.get("/api/search?q=test&limit=300")
        assert response.status_code == 422

    def test_search_valid_limit_range(self, client):
        """Test search with valid limit values."""
        # Minimum valid limit
        response = client.get("/api/search?q=test&limit=1")
        assert response.status_code == 200

        # Maximum valid limit
        response = client.get("/api/search?q=test&limit=200")
        assert response.status_code == 200


class TestSearchErrorHandling:
    """Test search error handling."""

    def test_search_explorer_not_initialized(self):
        """Test search endpoint when explorer is not initialized."""
        with patch("main.explorer", None):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            response = client.get("/api/search?q=test")
            assert response.status_code == 503
            assert response.json()["detail"] == "Explorer not initialized"

    def test_search_explorer_exception(self, client, mock_explorer):
        """Test search when explorer raises an exception."""
        mock_explorer.search_conversations.side_effect = Exception("Search error")

        response = client.get("/api/search?q=test")
        assert response.status_code == 500


class TestSearchResponseModel:
    """Test search response model validation."""

    def test_search_response_structure(self, client):
        """Test that search response has correct structure."""
        response = client.get("/api/search?q=test")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "conversations" in data
        assert "total_count" in data
        assert "query" in data

        # Correct types
        assert isinstance(data["conversations"], list)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["query"], str)

    def test_search_conversation_structure(self, client, mock_explorer):
        """Test structure of conversation objects in search results."""
        # Mock a conversation with all possible fields
        mock_conv = Mock(
            chat_id="conv1",
            created_at="2024-01-01T00:00:00",
            metadata_json={"source": "web", "user_id": "user123"},
            message_count=15,
            clusters=[
                Mock(name="Python"),
                Mock(name="Data Science"),
                Mock(name="Machine Learning"),
            ],
        )
        mock_explorer.search_conversations.return_value = [mock_conv]

        mock_summary = Mock(
            chat_id="conv1",
            summary="Detailed summary",
            request="Original request",
            languages=["python"],
            task="data_analysis",
            concerning_score=2,
            user_frustration=3,
            assistant_errors=["syntax_error"],
            metadata={"additional": "data"},
        )
        mock_explorer.get_summary.return_value = mock_summary

        response = client.get("/api/search?q=test")
        assert response.status_code == 200

        data = response.json()
        assert len(data["conversations"]) == 1

        conversation = data["conversations"][0]

        # Check all conversation fields
        assert conversation["id"] == "conv1"
        assert conversation["message_count"] == 15
        assert conversation["metadata"]["source"] == "web"
        assert conversation["metadata"]["user_id"] == "user123"

        # Check summary fields
        summary = conversation["summary"]
        assert summary["summary"] == "Detailed summary"
        assert summary["languages"] == ["python"]
        assert summary["user_frustration"] == 3

        # Check cluster names (should be limited to 3)
        assert len(conversation["cluster_names"]) == 3
        assert "Python" in conversation["cluster_names"]


class TestSearchPerformance:
    """Test search performance and edge cases."""

    def test_search_large_result_set(self, client, mock_explorer):
        """Test search with large result set and limiting."""
        # Mock a large number of results
        large_results = [
            Mock(
                chat_id=f"conv_{i}",
                created_at="2024-01-01T00:00:00",
                metadata_json={},
                message_count=10,
                clusters=[],
            )
            for i in range(1000)
        ]

        mock_explorer.search_conversations.return_value = large_results
        mock_explorer.get_summary.return_value = None

        response = client.get("/api/search?q=popular&limit=50")
        assert response.status_code == 200

        data = response.json()
        assert len(data["conversations"]) == 50  # Limited by the slice
        assert data["total_count"] == 1000  # Full count reported

    def test_search_special_characters(self, client):
        """Test search with special characters in query."""
        special_queries = [
            "python@2024",
            "how-to-debug",
            "error: syntax",
            "function()",
            "list[0]",
            "user&admin",
        ]

        for query in special_queries:
            response = client.get(f"/api/search?q={query}")
            # Should not fail with special characters
            assert response.status_code in [
                200,
                422,
            ]  # Either success or validation error
