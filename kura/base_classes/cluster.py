from abc import ABC, abstractmethod
from kura.summarisation import ConversationSummary
from kura.types import Cluster


class BaseClusterModel(ABC):
    @property
    @abstractmethod
    def checkpoint_filename(self) -> str:
        """The filename to use for checkpointing this model's output."""
        pass
    
    @abstractmethod
    async def cluster_summaries(
        self, summaries: list[ConversationSummary]
    ) -> list[Cluster]:
        pass

    # TODO : Add abstract method for hooks here once we start supporting it
