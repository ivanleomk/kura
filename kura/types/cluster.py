from pydantic import BaseModel, Field, computed_field
import uuid
from typing import Union
from kura.types.metadata import cluster_metadata_dict


class Cluster(BaseModel):
    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )
    name: str
    description: str
    chat_ids: list[str]
    parent_id: Union[str, None]
    metadata: cluster_metadata_dict

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
