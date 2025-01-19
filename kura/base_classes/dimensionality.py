from abc import ABC, abstractmethod

from kura.types import Cluster, ProjectedCluster


class BaseDimensionalityReduction(ABC):
    @abstractmethod
    async def reduce_dimensionality(
        self, clusters: list[Cluster]
    ) -> list[ProjectedCluster]:
        """
        This reduces the dimensionality of the individual clusters that we've created so we can visualise them in a lower dimension
        """
        pass
