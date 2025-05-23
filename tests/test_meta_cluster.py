import pytest
from pydantic import ValidationError
from kura.meta_cluster import ClusterLabel


def test_cluster_label_exact_match():
    """Test that ClusterLabel works with exact matches"""
    candidate_clusters = [
        "Code Assistance (Python & Rust)",
        "Data Analysis",
        "Creative Writing",
    ]

    validated = ClusterLabel.model_validate_json(
        '{"higher_level_cluster": "Code Assistance (Python & Rust)"}',
        context={"candidate_clusters": candidate_clusters},
    )

    assert validated.higher_level_cluster == "Code Assistance (Python & Rust)"


def test_fuzzy_match():
    """Test that ClusterLabel works with fuzzy matches above threshold"""
    candidate_clusters = [
        "Code Assistance (Python & Rust)",
        "Data Analysis",
        "Creative Writing",
    ]

    validated = ClusterLabel.model_validate_json(
        '{"higher_level_cluster": "Code Assistance (Python & Rust"}',
        context={"candidate_clusters": candidate_clusters},
    )

    assert validated.higher_level_cluster == "Code Assistance (Python & Rust)"


def test_no_match():
    """Test that ClusterLabel works with exact matches"""
    candidate_clusters = [
        "Code Assistance (Python & Rust)",
        "Data Analysis",
        "Creative Writing",
    ]

    with pytest.raises(ValidationError):
        ClusterLabel.model_validate_json(
            '{"higher_level_cluster": "Code Assistance"}',
            context={"candidate_clusters": candidate_clusters},
        )
