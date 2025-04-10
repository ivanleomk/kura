from pydantic import BaseModel
from typing import Union


class ConversationSummary(BaseModel):
    chat_id: str
    summary: str
    metadata: dict


class GeneratedSummary(BaseModel):
    summary: str


class ExtractedProperty(BaseModel):
    name: str
    value: Union[str, int, float, bool, list[str], list[int], list[float]]
