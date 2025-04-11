from kura.metadata import combine_cluster_metadata, combine_summary_metadata


def test_combine_metadata_single_item():
    metadata_list = [
        {"a": 1, "b": 2},
    ]
    combined_metadata = combine_summary_metadata(metadata_list)
    assert combined_metadata == {"a": [1], "b": [2]}


def test_combine_metadata():
    metadata_list = [
        {"a": 1, "b": 2, "c": True},
        {"a": 3, "b": 4, "c": False},
    ]
    combined_metadata = combine_summary_metadata(metadata_list)
    assert combined_metadata == {
        "a": [1, 3],
        "b": [2, 4],
        "c": [True, False],
    }


def test_combine_metadata_lists():
    metadata_list = [
        {"a": 1, "b": [2, 3], "c": ["foo", "bar"]},
        {"a": 3, "b": [3, 4], "c": ["baz", "qux"]},
    ]
    combined_metadata = combine_summary_metadata(metadata_list)
    assert combined_metadata == {
        "a": [1, 3],
        "b": [[2, 3], [3, 4]],
        "c": [["foo", "bar"], ["baz", "qux"]],
    }


def test_combine_cluster_metadata():
    metadata_list = [
        {"a": [1, 2, 3], "b": [[1, 2, 3], [4, 5, 6]], "c": [True, False, True]},
        {"a": [4, 5, 6], "b": [[1, 2, 3], [4, 5, 6]], "c": [False, True, False]},
    ]
    combined_metadata = combine_cluster_metadata(metadata_list)
    assert combined_metadata == {
        "a": [1, 2, 3, 4, 5, 6],
        "b": [[1, 2, 3], [4, 5, 6], [1, 2, 3], [4, 5, 6]],
        "c": [True, False, True, False, True, False],
    }
