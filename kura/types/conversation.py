from pydantic import BaseModel
from datetime import datetime
from typing import Literal
import json
import importlib


class Message(BaseModel):
    created_at: datetime
    role: Literal["user", "assistant"]
    content: str


class Conversation(BaseModel):
    chat_id: str
    created_at: datetime
    messages: list[Message]

    @classmethod
    def from_hf_dataset(
        cls,
        dataset_name: str,
        split: str = "train",
        chat_id_fn=lambda x: x["chat_id"],
        created_at_fn=lambda x: x["created_at"],
        messages_fn=lambda x: x["messages"],
    ) -> list["Conversation"]:
        if importlib.util.find_spec("datasets") is None:
            raise ImportError(
                "Please install hf datasets to load conversations from a dataset"
            )
        from datasets import load_dataset  # type: ignore

        dataset = load_dataset(dataset_name, split=split)
        return [
            Conversation(
                chat_id=chat_id_fn(conversation),
                created_at=created_at_fn(conversation),
                messages=messages_fn(conversation),
            )
            for conversation in dataset
        ]

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
