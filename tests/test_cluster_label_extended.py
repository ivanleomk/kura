import pytest
from pydantic import BaseModel, field_validator, ValidationInfo, ValidationError
from thefuzz import fuzz


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


def test_cluster_label_capitalization():
    """Test that ClusterLabel handles different capitalization."""
    candidate_clusters = [
        "Code Assistance (Python & Rust)",
        "Data Analysis",
        "Creative Writing",
    ]

    # Test with slightly different capitalization
    validated = ClusterLabel.model_validate_json(
        '{"higher_level_cluster": "Code Assistance (python & rust)"}',
        context={"candidate_clusters": candidate_clusters},
    )
    assert validated.higher_level_cluster == "Code Assistance (Python & Rust)"

def test_cluster_label_minor_differences():
    """Test that ClusterLabel handles slight variations."""
    candidate_clusters = [
        "Code Assistance (Python & Rust)",
        "Data Analysis",
        "Creative Writing",
    ]
    
    # Test with punctuation differences
    validated = ClusterLabel.model_validate_json(
        '{"higher_level_cluster": "Creative Writing!"}',
        context={"candidate_clusters": candidate_clusters},
    )
    assert validated.higher_level_cluster == "Creative Writing"


def test_cluster_label_below_threshold():
    """Test that ClusterLabel rejects matches below the threshold."""
    candidate_clusters = [
        "Data Science and Machine Learning",
        "Web Development",
        "Mobile Apps",
    ]

    # This is below the 90% threshold
    with pytest.raises(ValidationError):
        ClusterLabel.model_validate_json(
            '{"higher_level_cluster": "Data Science"}',
            context={"candidate_clusters": candidate_clusters},
        )


def test_cluster_label_on_threshold_boundary():
    """Test cases around the 90% similarity threshold."""
    # Create a controlled test where we know the similarity score
    # "ABCDEFGHIJ" and "ABCDEFGHI" have exactly 90% similarity
    candidate_clusters = ["ABCDEFGHIJ"]
    
    # Should pass at 90%
    validated = ClusterLabel.model_validate_json(
        '{"higher_level_cluster": "ABCDEFGHI"}',
        context={"candidate_clusters": candidate_clusters},
    )
    assert validated.higher_level_cluster == "ABCDEFGHIJ"
    
    # Should fail just below 90%
    with pytest.raises(ValidationError):
        ClusterLabel.model_validate_json(
            '{"higher_level_cluster": "ABCDEFGH"}',
            context={"candidate_clusters": candidate_clusters},
        )