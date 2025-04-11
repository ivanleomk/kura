from kura.types.metadata import metadata_dict, cluster_metadata_dict


def combine_summary_metadata(metadata_list: list[metadata_dict]) -> metadata_dict:
    combined_metadata = {}

    assert len(metadata_list) > 0

    for key, value in metadata_list[0].items():
        combined_metadata[key] = [value]

    for metadata in metadata_list[1:]:
        for key, value in metadata.items():
            if key not in combined_metadata:
                raise ValueError(
                    f"All items must have the same metadata keys - {key} not found in {metadata}"
                )
            combined_metadata[key].append(value)

    return combined_metadata


def combine_cluster_metadata(
    metadata_list: list[cluster_metadata_dict],
) -> cluster_metadata_dict:
    combined_metadata = {}

    assert len(metadata_list) > 0

    for key, value in metadata_list[0].items():
        combined_metadata[key] = value

    for metadata in metadata_list[1:]:
        for key, value in metadata.items():
            combined_metadata[key].extend(value)

    return combined_metadata
