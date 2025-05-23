from abc import ABC, abstractmethod
from kura.summarisation import ConversationSummary
from kura.types import Cluster


class BaseClusterModel(ABC):
    @abstractmethod
    async def cluster_summaries(
        self, summaries: list[ConversationSummary]
    ) -> list[Cluster]:
        pass

    # TODO : Add abstract method for hooks here once we start supporting it
