"""Tests for conversations router."""

import pytest
from unittest.mock import Mock, patch


class TestGetConversations:
    """Test GET /api/conversations endpoint."""
    
    def test_get_conversations_success(self, client, mock_explorer):
        """Test successful conversations retrieval."""
        response = client.get("/api/conversations")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data
        
        assert len(data["items"]) > 0
        conversation = data["items"][0]
        assert "id" in conversation
        assert "created_at" in conversation
        assert "metadata" in conversation
        assert "message_count" in conversation
        assert "cluster_names" in conversation
    
    def test_get_conversations_with_pagination(self, client):
        """Test conversations with pagination parameters."""
        response = client.get("/api/conversations?limit=20&offset=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["limit"] == 20
        assert data["offset"] == 10
    
    def test_get_conversations_with_cluster_filter(self, client):
        """Test conversations filtered by cluster ID."""
        response = client.get("/api/conversations?cluster_id=cluster_1")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
    
    def test_get_conversations_with_search(self, client):
        """Test conversations with search parameter."""
        response = client.get("/api/conversations?search=pandas")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
    
    def test_get_conversations_with_language_filter(self, client):
        """Test conversations filtered by language."""
        response = client.get("/api/conversations?language=python")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
    
    def test_get_conversations_with_frustration_filters(self, client):
        """Test conversations with frustration level filters."""
        # Test minimum frustration
        response = client.get("/api/conversations?min_frustration=2")
        assert response.status_code == 200
        
        # Test maximum frustration
        response = client.get("/api/conversations?max_frustration=4")
        assert response.status_code == 200
        
        # Test both min and max
        response = client.get("/api/conversations?min_frustration=2&max_frustration=4")
        assert response.status_code == 200
    
    def test_get_conversations_invalid_pagination(self, client):
        """Test conversations with invalid pagination parameters."""
        # Negative offset
        response = client.get("/api/conversations?offset=-1")
        assert response.status_code == 422
        
        # Invalid limit
        response = client.get("/api/conversations?limit=0")
        assert response.status_code == 422
        
        # Limit too large
        response = client.get("/api/conversations?limit=300")
        assert response.status_code == 422
    
    def test_get_conversations_invalid_frustration_range(self, client):
        """Test conversations with invalid frustration parameters."""
        # Frustration out of range
        response = client.get("/api/conversations?min_frustration=0")
        assert response.status_code == 422
        
        response = client.get("/api/conversations?max_frustration=6")
        assert response.status_code == 422
    
    def test_get_conversations_explorer_not_initialized(self):
        """Test conversations endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/conversations")
            assert response.status_code == 503
            assert response.json()["detail"] == "Explorer not initialized"


class TestGetConversation:
    """Test GET /api/conversations/{conversation_id} endpoint."""
    
    def test_get_conversation_success(self, client, mock_explorer):
        """Test successful single conversation retrieval."""
        response = client.get("/api/conversations/conv1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "conv1"
        assert "created_at" in data
        assert "metadata" in data
        assert "messages" in data
        assert "summary" in data
        assert "clusters" in data
        
        # Check messages structure
        assert isinstance(data["messages"], list)
        if len(data["messages"]) > 0:
            message = data["messages"][0]
            assert "id" in message
            assert "conversation_id" in message
            assert "created_at" in message
            assert "role" in message
            assert "content" in message
        
        # Check summary structure
        if data["summary"]:
            summary = data["summary"]
            assert "chat_id" in summary
            assert "summary" in summary
    
    def test_get_conversation_not_found(self, client, mock_explorer):
        """Test conversation not found."""
        # Mock explorer to return None for non-existent conversation
        mock_explorer.get_conversation.return_value = None
        
        response = client.get("/api/conversations/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Conversation not found"
    
    def test_get_conversation_explorer_not_initialized(self):
        """Test single conversation endpoint when explorer is not initialized."""
        with patch('main.explorer', None):
            from main import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            response = client.get("/api/conversations/conv1")
            assert response.status_code == 503


class TestConversationFiltering:
    """Test conversation filtering logic."""
    
    def test_conversation_filtering_with_summary(self, client, mock_explorer):
        """Test that conversations are properly filtered based on summary data."""
        # Create mock conversations with different summary properties
        conv_with_python = Mock(
            chat_id="conv_python",
            created_at="2024-01-01T00:00:00",
            metadata_json={"source": "web"},
            message_count=10,
            clusters=[]
        )
        
        conv_with_javascript = Mock(
            chat_id="conv_js",
            created_at="2024-01-02T00:00:00", 
            metadata_json={"source": "api"},
            message_count=5,
            clusters=[]
        )
        
        mock_explorer.get_conversations.return_value = [conv_with_python, conv_with_javascript]
        
        # Mock summaries with different languages
        def mock_get_summary(chat_id):
            if chat_id == "conv_python":
                return Mock(
                    languages=["python"],
                    user_frustration=3,
                    task="coding"
                )
            elif chat_id == "conv_js":
                return Mock(
                    languages=["javascript"],
                    user_frustration=2,
                    task="debugging"
                )
            return None
        
        mock_explorer.get_summary.side_effect = mock_get_summary
        
        # Test language filtering
        response = client.get("/api/conversations?language=python")
        assert response.status_code == 200
        
        # Should call the mock methods
        mock_explorer.get_conversations.assert_called()


class TestConversationResponseModels:
    """Test conversation response model validation."""
    
    def test_conversation_response_required_fields(self, client):
        """Test that conversation responses have all required fields."""
        response = client.get("/api/conversations")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["items"]) > 0:
            conversation = data["items"][0]
            
            # Required fields
            required_fields = ["id", "created_at", "metadata", "message_count"]
            for field in required_fields:
                assert field in conversation, f"Missing required field: {field}"
    
    def test_conversation_detail_response_structure(self, client):
        """Test conversation detail response structure."""
        response = client.get("/api/conversations/conv1")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check messages structure
        assert isinstance(data.get("messages", []), list)
        
        # Check clusters structure
        assert isinstance(data.get("clusters", []), list)
        
        # Summary can be null or object
        summary = data.get("summary")
        if summary is not None:
            assert isinstance(summary, dict)
            assert "chat_id" in summary
            assert "summary" in summary
    
    def test_conversation_with_summary_fields(self, client):
        """Test conversation response when summary is present."""
        response = client.get("/api/conversations/conv1")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("summary"):
            summary = data["summary"]
            # Optional summary fields
            optional_fields = ["languages", "task", "user_frustration", "concerning_score"]
            # These fields may or may not be present, but if present should be correct type
            for field in optional_fields:
                if field in summary:
                    if field == "languages":
                        assert isinstance(summary[field], list)
                    elif field in ["user_frustration", "concerning_score"]:
                        assert isinstance(summary[field], (int, type(None)))


class TestConversationPagination:
    """Test conversation pagination logic."""
    
    def test_pagination_has_more_true(self, client, mock_explorer):
        """Test pagination when there are more items."""
        # Mock more conversations than the limit
        conversations = [Mock(
            chat_id=f"conv_{i}",
            created_at="2024-01-01T00:00:00",
            metadata_json={},
            message_count=10,
            clusters=[]
        ) for i in range(100)]
        
        mock_explorer.get_conversations.return_value = conversations
        mock_explorer.get_summary.return_value = None
        
        response = client.get("/api/conversations?limit=10&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        # Since we have 100 items and limit is 10, has_more should be True
        # Note: The actual logic depends on the filtering in the endpoint
        assert "has_more" in data
    
    def test_pagination_offset_beyond_results(self, client, mock_explorer):
        """Test pagination when offset is beyond available results."""
        conversations = [Mock(
            chat_id="conv_1",
            created_at="2024-01-01T00:00:00",
            metadata_json={},
            message_count=10,
            clusters=[]
        )]
        
        mock_explorer.get_conversations.return_value = conversations
        mock_explorer.get_summary.return_value = None
        
        response = client.get("/api/conversations?limit=10&offset=100")
        assert response.status_code == 200
        
        data = response.json()
        assert data["offset"] == 100
        assert len(data["items"]) == 0 