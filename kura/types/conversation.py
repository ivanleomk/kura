import json
from datetime import datetime, timezone
from typing import Literal, Union

from pydantic import BaseModel


class Message(BaseModel):
    created_at: datetime
    role: Literal["user", "assistant"]
    content: str


class Conversation(BaseModel):
    chat_id: str
    created_at: datetime
    messages: list[Message]

    # TODO Surely there's a better way than nesting datetime calls?
    @staticmethod
    def formatDate(timestamp: Union[str, int, float]) -> datetime:
        """Convert ISO string or timestamp to a datetime object."""
        if isinstance(timestamp, (int, float)):
            # Handle Unix timestamps
            return datetime.fromisoformat(
                datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(
                    timespec="milliseconds"
                )
            )
        else:
            # Handle ISO format strings
            return datetime.fromisoformat(
                datetime.fromisoformat(timestamp).isoformat(timespec="milliseconds")
            )

    @classmethod
    def from_claude_conversation_dump(cls, file_path: str) -> list["Conversation"]:
        with open(file_path, "r") as f:
            return [
                Conversation(
                    chat_id=conversation["uuid"],
                    created_at=Conversation.formatDate(conversation["created_at"]),
                    messages=[
                        Message(
                            created_at=Conversation.formatDate(message["created_at"]),
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

    @classmethod
    def from_chatgpt_conversation_dump(cls, file_path: str) -> list["Conversation"]:
        with open(file_path, "r") as f:
            convs = []
            data = json.load(f)

            for conversation in data:
                chat_id = conversation.get("conversation_id")
                created_at = Conversation.formatDate(conversation.get("create_time"))
                messages = []

                for _, message_object in conversation.get("mapping", {}).items():
                    message = message_object.get("message")
                    if not message:
                        continue

                    role = message.get("author", {}).get("role")
                    if role in {"system", "tool"}:
                        continue

                    content = message.get("content", {})
                    msg_text = (
                        content.get("parts", [])[0].strip()
                        if content.get("content_type") == "text"
                        and content.get("parts")
                        else ""
                    )

                    msg_created_at = Conversation.formatDate(message.get("create_time"))
                    messages.append(
                        Message(
                            created_at=msg_created_at,
                            role=role,
                            content=msg_text,
                        )
                    )

                convs.append(
                    Conversation(
                        chat_id=chat_id,
                        created_at=created_at,
                        messages=messages,
                    )
                )

            return convs
