from pydantic import BaseModel, Field, computed_field
import uuid
from typing import Union


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
    name: str = Field(..., description="A short, imperative sentence (at most ten words) that captures the user's request and distinguishes this cluster from others. Should be specific but reflective of most statements in the group. Examples: 'Brainstorm ideas for a birthday party' or 'Generate blog spam for gambling websites'")
    summary: str = Field(..., description="A clear, precise, two-sentence description in past tense that captures the essence of the clustered statements and distinguishes them from contrastive examples. Should be specific to this group without including PII or proper nouns")


class ClusterTreeNode(BaseModel):
    id: str
    name: str
    description: str
    count: int
    children: list[str]
