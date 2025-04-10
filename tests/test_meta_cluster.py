import pytest
from pydantic import ValidationError
from thefuzz import fuzz
from kura.meta_cluster import ClusterLabel
from kura.types.cluster import Cluster


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


# def test_cluster_label_fuzzy_match():
#     """Test that ClusterLabel works with fuzzy matches above threshold"""
#     candidate_clusters = [
#         "Code Assistance (Python & Rust)",
#         "Data Analysis",
#         "Creative Writing",
#     ]

#     # Create validation context with candidate clusters
#     context = {"candidate_clusters": candidate_clusters}

#     # Should work with fuzzy match (small typo)
#     validated = ClusterLabel.model_validate(
#         {"higher_level_cluster": "Code Assistance (Python & Rusty)"}, context=context
#     )
#     assert validated.higher_level_cluster == "Code Assistance (Python & Rust)"

#     # Should work with another minor variation
#     validated = ClusterLabel.model_validate(
#         {"higher_level_cluster": "Code Assistance (Python and Rust)"}, context=context
#     )
#     assert validated.higher_level_cluster == "Code Assistance (Python & Rust)"


# def test_cluster_label_no_match():
#     """Test that ClusterLabel raises an error when no match is close enough"""
#     candidate_clusters = [
#         "Code Assistance (Python & Rust)",
#         "Data Analysis",
#         "Creative Writing",
#     ]

#     # Create validation context with candidate clusters
#     context = {"candidate_clusters": candidate_clusters}

#     # Should fail when match is too different
#     with pytest.raises(ValidationError):
#         ClusterLabel.model_validate(
#             {"higher_level_cluster": "Something Completely Different"}, context=context
#         )


# def test_fuzzy_similarity_threshold():
#     """Test different similarity thresholds for fuzzy matching"""
#     text1 = "Code Assistance (Python & Rust)"
#     text2 = "Code Assistance (Python and Rust)"
#     text3 = "Something Completely Different"

#     # These should be above our threshold (90%)
#     similarity1 = fuzz.ratio(text1, text2) / 100.0
#     assert similarity1 >= 0.9

#     # This should be below our threshold
#     similarity2 = fuzz.ratio(text1, text3) / 100.0
#     assert similarity2 < 0.9
