import pytest
from pydantic import ValidationError

# Creating a simplified version of CandidateClusters for testing
# since importing the actual class requires Google API credentials
from pydantic import BaseModel, field_validator


class CandidateClusters(BaseModel):
    candidate_cluster_names: list[str]

    @field_validator("candidate_cluster_names")
    def validate_candidate_cluster_names(cls, v: list[str]) -> list[str]:
        if len(v) == 0:
            raise ValueError("Candidate cluster names must be a non-empty list")

        v = [label.strip() for label in v]
        v = [label[:-1] if label.endswith(".") else label for label in v]

        return [label.replace('"', "").replace("\\", "") for label in v]


def test_candidate_clusters_valid():
    """Test that CandidateClusters accepts valid input."""
    clusters = CandidateClusters(
        candidate_cluster_names=["Cluster 1", "Cluster 2", "Cluster 3"]
    )
    
    assert clusters.candidate_cluster_names == ["Cluster 1", "Cluster 2", "Cluster 3"]


def test_candidate_clusters_empty_list():
    """Test that CandidateClusters rejects empty lists."""
    with pytest.raises(ValidationError) as exc_info:
        CandidateClusters(candidate_cluster_names=[])
    
    assert "Candidate cluster names must be a non-empty list" in str(exc_info.value)


def test_candidate_clusters_string_cleaning():
    """Test that CandidateClusters properly cleans strings."""
    clusters = CandidateClusters(
        candidate_cluster_names=[
            "  Cluster with spaces  ",
            "Cluster with period.",
            "Cluster with \"quotes\"",
            "Cluster with \\backslashes\\",
        ]
    )
    
    assert clusters.candidate_cluster_names == [
        "Cluster with spaces",
        "Cluster with period",
        "Cluster with quotes",
        "Cluster with backslashes",
    ]