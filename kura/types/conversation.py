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
                            created_at=datetime.fromisoformat(
                                message["created_at"].replace("Z", "+00:00")
                            ),
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
                        for message in sorted(
                            conversation["chat_messages"],
                            key=lambda x: (
                                datetime.fromisoformat(
                                    x["created_at"].replace("Z", "+00:00")
                                ),
                                0 if x["sender"] == "human" else 1,
                            ),
                        )
                    ],
                )
                for conversation in json.load(f)
            ]
