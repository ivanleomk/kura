import pytest
import uuid
from pydantic import BaseModel, Field, computed_field
from typing import Union

# Re-implementation of the models for testing
class Cluster(BaseModel):
    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )
    name: str
    description: str
    chat_ids: list[str]
    parent_id: Union[str, None]

    @computed_field
    def count(self) -> int:
        return len(self.chat_ids)


class GeneratedCluster(BaseModel):
    name: str
    summary: str


class ClusterTreeNode(BaseModel):
    id: str
    name: str
    description: str
    count: int
    children: list[str]


def test_cluster_initialization():
    """Test that Cluster objects initialize correctly with required fields."""
    cluster = Cluster(
        name="Test Cluster",
        description="A test cluster",
        chat_ids=["chat1", "chat2", "chat3"],
        parent_id=None,
    )
    
    assert cluster.name == "Test Cluster"
    assert cluster.description == "A test cluster"
    assert cluster.chat_ids == ["chat1", "chat2", "chat3"]
    assert cluster.parent_id is None
    assert len(cluster.id) > 0  # ID should be auto-generated


def test_cluster_count_computed_field():
    """Test that the count computed field works correctly."""
    cluster = Cluster(
        name="Test Cluster",
        description="A test cluster",
        chat_ids=["chat1", "chat2", "chat3"],
        parent_id=None,
    )
    
    assert cluster.count == 3
    
    empty_cluster = Cluster(
        name="Empty Cluster",
        description="An empty cluster",
        chat_ids=[],
        parent_id=None,
    )
    
    assert empty_cluster.count == 0


def test_generated_cluster():
    """Test that GeneratedCluster objects initialize correctly."""
    gen_cluster = GeneratedCluster(
        name="Generated Cluster", 
        summary="This is a summary"
    )
    
    assert gen_cluster.name == "Generated Cluster"
    assert gen_cluster.summary == "This is a summary"


def test_cluster_tree_node():
    """Test that ClusterTreeNode objects initialize correctly."""
    node = ClusterTreeNode(
        id="123",
        name="Tree Node",
        description="A tree node",
        count=5,
        children=["child1", "child2"],
    )
    
    assert node.id == "123"
    assert node.name == "Tree Node"
    assert node.description == "A tree node"
    assert node.count == 5
    assert node.children == ["child1", "child2"]


def test_id_generation():
    """Test that IDs are unique for different cluster instances."""
    cluster1 = Cluster(
        name="Cluster 1",
        description="First cluster",
        chat_ids=["chat1"],
        parent_id=None,
    )
    
    cluster2 = Cluster(
        name="Cluster 2",
        description="Second cluster",
        chat_ids=["chat2"],
        parent_id=None,
    )
    
    assert cluster1.id != cluster2.id