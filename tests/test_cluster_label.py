import pytest
from pydantic import BaseModel, field_validator, ValidationInfo, ValidationError
from thefuzz import fuzz
import re

# Simplified ClusterLabel class for testing
class ClusterLabel(BaseModel):
    higher_level_cluster: str

    @field_validator("higher_level_cluster")
    def validate_higher_level_cluster(cls, v: str, info: ValidationInfo) -> str:
        candidate_clusters = info.context["candidate_clusters"]  # pyright: ignore

        # Exact match check
        if v in candidate_clusters:
            return v

        # Fuzzy match check with 90% similarity threshold
        for candidate in candidate_clusters:
            similarity = fuzz.ratio(v, candidate)
            if similarity >= 90:  # 90% similarity threshold
                return candidate

        # If no match found
        raise ValueError(
            f"""
            Invalid higher-level cluster: |{v}|
            
            Valid clusters are:
            {", ".join(f"|{c}|" for c in candidate_clusters)} 
            """
        )
        return v


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
    """Test that ClusterLabel fails with non-matching inputs"""
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