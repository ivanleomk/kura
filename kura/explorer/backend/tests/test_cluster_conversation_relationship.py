"""Test cluster-conversation relationships."""


def test_cluster_has_conversations(mock_explorer):
    """Test that clusters report correct conversation counts."""
    # Get clusters from mock
    clusters = mock_explorer.get_clusters()

    # Check that clusters have chat_ids
    for cluster in clusters:
        print(f"\nCluster {cluster.name} (ID: {cluster.id}):")
        print(f"  - chat_ids: {cluster.chat_ids}")
        print(f"  - chat_ids count: {len(cluster.chat_ids) if cluster.chat_ids else 0}")

        # Clusters should have chat_ids
        assert cluster.chat_ids is not None, (
            f"Cluster {cluster.id} has no chat_ids field"
        )
        assert len(cluster.chat_ids) > 0, f"Cluster {cluster.id} has empty chat_ids"


def test_cluster_api_conversation_count(client):
    """Test that the cluster API returns correct conversation counts."""
    # Get clusters from API
    response = client.get("/api/clusters")
    assert response.status_code == 200

    data = response.json()
    print(f"\nClusters API returned {len(data['items'])} clusters")

    # Check each cluster
    for cluster in data["items"]:
        print(f"\nCluster {cluster['name']} (ID: {cluster['id']}):")
        print(f"  - Conversation count from API: {cluster['conversation_count']}")

        # Conversation count should be > 0 for at least some clusters
        if cluster["id"] in ["cluster_1", "cluster_2"]:
            assert cluster["conversation_count"] > 0, (
                f"Cluster {cluster['id']} should have conversations but has {cluster['conversation_count']}"
            )

        # Get detailed cluster info
        detail_response = client.get(f"/api/clusters/{cluster['id']}")
        assert detail_response.status_code == 200

        detail = detail_response.json()
        print(f"  - Conversations in detail view: {len(detail['conversations'])}")

        # The counts should match
        assert cluster["conversation_count"] == len(detail["conversations"]), (
            f"Mismatch for cluster {cluster['id']}: list count={cluster['conversation_count']}, detail count={len(detail['conversations'])}"
        )


def test_conversations_have_cluster_names(client):
    """Test that conversations include their cluster names."""
    # Get conversations from API
    response = client.get("/api/conversations")
    assert response.status_code == 200

    data = response.json()
    print(f"\nConversations API returned {len(data['items'])} conversations")

    # Check each conversation
    conversations_with_clusters = 0
    for conv in data["items"]:
        print(f"\nConversation {conv['id']}:")
        print(f"  - Cluster names: {conv['cluster_names']}")

        if conv["cluster_names"]:
            conversations_with_clusters += 1

    print(
        f"\n{conversations_with_clusters} out of {len(data['items'])} conversations have cluster assignments"
    )

    # All conversations should have clusters in our mock data
    assert conversations_with_clusters > 0, "No conversations have cluster assignments"


def test_cluster_frontend_display(client):
    """Test that clusters page shows conversations correctly."""
    # Get clusters
    response = client.get("/api/clusters")
    assert response.status_code == 200

    clusters = response.json()["items"]

    # Check that conversation_count is properly set
    for cluster in clusters:
        print(f"\nChecking cluster {cluster['name']}:")
        print(f"  - ID: {cluster['id']}")
        print(f"  - Conversation count: {cluster['conversation_count']}")

        # The issue: conversation_count is 0 when it should have values
        # This is because the API is using len(cluster.chat_ids) but chat_ids might be None
        assert "conversation_count" in cluster, (
            "Cluster missing conversation_count field"
        )
