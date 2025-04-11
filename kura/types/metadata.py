from typing import Union

metadata_dict = dict[
    str, Union[str, int, float, bool, list[str], list[int], list[float]]
]

cluster_metadata_dict = dict[
    str,
    Union[
        list[int],
        list[str],
        list[float],
        list[bool],
        list[list[int]],
        list[list[str]],
        list[list[float]],
    ],
]
