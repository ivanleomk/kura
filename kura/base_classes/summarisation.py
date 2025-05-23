from abc import ABC, abstractmethod

from kura.types import ConversationSummary, Conversation
from typing import Union


class BaseSummaryModel(ABC):
    @abstractmethod
    async def summarise(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
        """Summarise the conversations into a list of ConversationSummary"""
        pass

    @abstractmethod
    async def summarise_conversation(
        self, conversation: Conversation
    ) -> ConversationSummary:
        """Summarise a single conversation into a single string"""
        pass

    @abstractmethod
    async def apply_hooks(
        self, conversation: Conversation
    ) -> dict[str, Union[str, int, float, bool, list[str], list[int], list[float]]]:
        """Apply hooks to the conversation summary"""
        # Assert that the implementation of the class has a hooks attribute so we can call it in summarise_conversation
        assert hasattr(self, "hooks")
        pass
