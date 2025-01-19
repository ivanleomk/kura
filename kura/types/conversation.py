from pydantic import BaseModel
from datetime import datetime
from typing import Literal
import json


class Message(BaseModel):
    created_at: datetime
    role: Literal["user", "assistant"]
    content: str


class Conversation(BaseModel):
    chat_id: str
    created_at: datetime
    messages: list[Message]

    @classmethod
    def from_claude_conversation_dump(cls, file_path: str) -> list["Conversation"]:
        with open(file_path, "r") as f:
            return [
                Conversation(
                    chat_id=conversation["uuid"],
                    created_at=conversation["created_at"],
                    messages=[
                        Message(
                            created_at=message["created_at"],
                            role="user"
                            if message["sender"] == "human"
                            else "assistant",
                            content="\n".join(
                                [
                                    item["text"]
                                    for item in message["content"]
                                    if item["type"] == "text"
                                ]
                            ),
                        )
                        for message in conversation["chat_messages"]
                    ],
                )
                for conversation in json.load(f)
            ]
