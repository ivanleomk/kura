from pydantic import BaseModel, Field
from typing import Optional, Union, List

class GeneratedSummary(BaseModel):
    summary: str = Field(..., description="A clear and concise summary of the conversation in at most two sentences, avoiding phrases like 'Based on the conversation' and excluding proper nouns or PII")
    request: Optional[str] = Field(None, description="The user's overall request for the assistant")
    languages: Optional[List[str]] = Field(None, description="Main languages present in the conversation including human and programming languages (e.g., ['english', 'arabic', 'python', 'javascript'])")
    task: Optional[str] = Field(None, description="The task the model is being asked to perform")
    concerning_score: Optional[int] = Field(None, ge=1, le=5, description="Safety concern rating from 1-5 scale")
    user_frustration: Optional[int] = Field(None, ge=1, le=5, description="User frustration rating from 1-5 scale")
    assistant_errors: Optional[List[str]] = Field(None, description="List of errors the assistant made")

class ConversationSummary(GeneratedSummary):
    chat_id: str
    metadata: dict

class ExtractedProperty(BaseModel):
    name: str
    value: Union[str, int, float, bool, List[str], List[int], List[float]]
