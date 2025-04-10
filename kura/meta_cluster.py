from kura.base_classes import (
    BaseMetaClusterModel,
    BaseEmbeddingModel,
    BaseClusteringMethod,
)
import math
from kura.types.cluster import Cluster, GeneratedCluster
from kura.embedding import OpenAIEmbeddingModel
from kura.k_means import KmeansClusteringMethod
import instructor
from google.genai import Client
from tqdm.asyncio import tqdm_asyncio
from asyncio import Semaphore
from pydantic import BaseModel, field_validator, ValidationInfo
import re
from thefuzz import fuzz


class CandidateClusters(BaseModel):
    candidate_cluster_names: list[str]

    @field_validator("candidate_cluster_names")
    def validate_candidate_cluster_names(
        cls, v: list[str], info: ValidationInfo
    ) -> list[str]:
        if len(v) == 0:
            raise ValueError("Candidate cluster names must be a non-empty list")

        v = [label.strip() for label in v]
        v = [label[:-1] if label.endswith(".") else label for label in v]

        return [re.sub(r"\\{1,}", "", label.replace('"', "")) for label in v]


class ClusterLabel(BaseModel):
    higher_level_cluster: str

    @field_validator("higher_level_cluster")
    def validate_higher_level_cluster(cls, v: str, info: ValidationInfo) -> str:
        candidate_clusters = info.context["candidate_clusters"]  # pyright: ignore

        # Exact match check
        if v in candidate_clusters:
            return v

        # Fuzzy match check with 90% similarity threshold
        for candidate in candidate_clusters:
            similarity = fuzz.ratio(v, candidate)
            if similarity >= 90:  # 90% similarity threshold
                return candidate

        # If no match found
        raise ValueError(
            f"""
            Invalid higher-level cluster: |{v}|
            
            Valid clusters are:
            {", ".join(f"|{c}|" for c in candidate_clusters)} 
            """
        )
        return v


class MetaClusterModel(BaseMetaClusterModel):
    def __init__(
        self,
        max_concurrent_requests: int = 50,
        client=instructor.from_genai(Client(), use_async=True),
        model="gemini-2.0-flash",
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
        clustering_model: BaseClusteringMethod = KmeansClusteringMethod(12),
    ):
        self.max_concurrent_requests = max_concurrent_requests
        self.client = client
        self.embedding_model = embedding_model
        self.clustering_model = clustering_model
        self.model = model

    async def generate_candidate_clusters(
        self, clusters: list[Cluster], sem: Semaphore
    ) -> list[str]:
        async with sem:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": """
                You are tasked with creating higher-level cluster names based on a given list of clusters and their descriptions. Your goal is to come up with broader categories that could encompass one or more of the provided clusters

                First, review the list of clusters and their descriptions:
                <cluster_list>
                    {% for cluster in clusters %}
                    <cluster>{{ cluster.name }}: {{ cluster.description }}</cluster>
                    {% endfor %}
                </cluster_list>

                Your task is to create at most {{ desired_number }} higher-level cluster names that could potentially include one or more of the provided clusters. These higher-level clusters should represent broader categories or themes that emerge from the given clusters, while remaining as specific as possible. If there are many clusters with a specific theme, ensure that the higher-level cluster name remains the maximum level of specificity. You are helping to organize user behavior data in order to improve safety, monitoring, and observability. You can generate less than {{ desired_number }} names if you feel that fewer are appropriate and accurately capture the clusters. 

                Guidelines for creating higher-level clusters names
                1. Analyze the themes, topics or characteristics common to multiple clusters.
                2. Create names that are specific enough to be meaningful but but not so specific that they can't meaningfully represent many different clusters. Avoid overly general or vague terms, and do not hesitate to describe socially harmful or sensitive topics (in fact, clusters that clearly describe harmful behavior are slightly preferred); specificity is necessary for observability and enforcement.
                3. Ensure that the higher-level cluster names are distinct from one another.
                4. Use clear, concise, and descriptive language for the cluster names. Assume neither good nor bad faith for the content in the clusters.

                Think about the relationships between the given clusters and potential overarching themes. 
                
                Focus on creating meaningful, distinct and precise ( but not overly specific ) higher-level cluster names that could encompass multiple sub-clusters.
                """.strip(),
                    },
                ],
                response_model=CandidateClusters,
                context={
                    "clusters": clusters,
                    "desired_number": math.ceil(len(clusters) / 2)
                    if len(clusters)
                    >= 3  # If we have two clusters we just merge them tbh
                    else 1,
                },
                max_retries=3,
            )
            return resp.candidate_cluster_names

    async def label_cluster(self, cluster: Cluster, candidate_clusters: list[str]):
        async with self.sem:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": """
You are tasked with categorizing a specific cluster into one of the provided higher-level clusters for observability, monitoring, and content moderation. Your goal is to determine which higher-level cluster best fits the given specific cluster based on its name and description.

First, here are the ONLY valid higher-level clusters you may select from:
<higher_level_clusters>
{% for cluster in candidate_clusters %}
<higher_level_cluster>{{ cluster }}</higher_level_cluster>
{% endfor %}
</higher_level_clusters>

Here is the specific cluster to categorize:
<specific_cluster>
Name: {{ cluster.name }}
Description: {{ cluster.description }}
</specific_cluster>

RULES:
1. You MUST select EXACTLY ONE higher-level cluster from the provided list
2. You MUST output the higher-level cluster name EXACTLY as written - no modifications allowed
3. You MUST NOT create new cluster names or combinations
4. You MUST NOT output any additional text or explanations
5. You MUST NOT use partial matches or approximate names

CLASSIFICATION PROCESS:
1. First, record the exact list of valid higher-level clusters
2. Read the specific cluster's name and description carefully
3. Compare the specific cluster's key characteristics against each valid higher-level cluster
4. Select the single most appropriate higher-level cluster that encompasses the specific cluster
5. Verify your selected cluster exactly matches one from the valid list
6. Output ONLY the selected higher-level cluster name, exactly as it appeared in the valid list

Here is the specific cluster to categorize:

<specific_cluster>
Name: {{ cluster.name }}
Description: {{ cluster.description }}
</specific_cluster>

Based on this information, determine the most appropriate higher-level cluster and provide your answer as instructed.
                        """,
                    }
                ],
                response_model=ClusterLabel,
                context={
                    "cluster": cluster,
                    "candidate_clusters": candidate_clusters,
                },
                max_retries=3,
            )
            return {
                "cluster": cluster,
                "label": resp.higher_level_cluster,
            }

    async def rename_cluster_group(self, clusters: list[Cluster]) -> list[Cluster]:
        async with self.sem:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are tasked with summarizing a group of related cluster names into a short, precise, and accurate overall description and name. Your goal is to create a concise summary that captures the essence of these clusters

                        The cluster name should be at most ten words long (perhaps less) and be specific but also reflective of most of the clusters that comprise them. The cluster name should be a sentence in the imperative that captures the user's request. For example, 'Brainstorm ideas for a birthday party' or 'Help me find a new job are good examples.

                        Do not shy away from describing socially harmful or sensitive topics. For instance, "Write fantasy sexual roleplay with octopi and monsters", "Generate blog spam for gambling websites", or "Assist with high school math homework" would be better than "Write erotic content" or "Help with homework". Be as descriptive as possible and assume neither good nor bad faith. Do not hesitate to identify and describe socially harmful or sensitive topics specifically; specificity is necessary for monitoring.

                        Ensure your summary and name accurately represent the clusters and are specific to the clusters.
                        """,
                    },
                    {
                        "role": "user",
                        "content": """
                        Here are the related cluster names
                        <clusters>
                            {% for cluster in clusters %}
                                <cluster>{{ cluster.name }}: {{ cluster.description }}</cluster>
                            {% endfor %}
                        </clusters>
                        """,
                    },
                ],
                context={"clusters": clusters},
                response_model=GeneratedCluster,
            )

            res = []

            new_cluster = Cluster(
                name=resp.name,
                description=resp.summary,
                chat_ids=[
                    chat_id for cluster in clusters for chat_id in cluster.chat_ids
                ],
                parent_id=None,
            )

            res.append(new_cluster)

            for cluster in clusters:
                res.append(
                    Cluster(
                        id=cluster.id,
                        name=cluster.name,
                        description=cluster.description,
                        chat_ids=cluster.chat_ids,
                        parent_id=new_cluster.id,
                    )
                )

            return res

    async def generate_meta_clusters(self, clusters: list[Cluster]) -> list[Cluster]:
        candidate_labels = await self.generate_candidate_clusters(
            clusters, Semaphore(self.max_concurrent_requests)
        )

        cluster_labels = await tqdm_asyncio.gather(
            *[self.label_cluster(cluster, candidate_labels) for cluster in clusters],
            disable=True,
        )

        label_to_clusters = {}
        for label in cluster_labels:
            if label["label"] not in label_to_clusters:
                label_to_clusters[label["label"]] = []

            label_to_clusters[label["label"]].append(label["cluster"])

        new_clusters = await tqdm_asyncio.gather(
            *[
                self.rename_cluster_group(cluster)
                for cluster in label_to_clusters.values()
            ],
            disable=True,
        )

        res = []
        for new_cluster in new_clusters:
            res.extend(new_cluster)

        return res

    async def reduce_clusters(self, clusters: list[Cluster]) -> list[Cluster]:
        """
        This takes in a list of existing clusters and generates a few higher order clusters that are more general. This represents a single iteration of the meta clustering process.

        In the event that we have a single cluster, we will just return a new higher level cluster which has the same name as the original cluster. ( This is an edge case which we should definitely handle better )
        """
        if len(clusters) == 1:
            print("Only one cluster, returning it as a meta cluster")
            new_cluster = Cluster(
                name=clusters[0].name,
                description=clusters[0].description,
                chat_ids=clusters[0].chat_ids,
                parent_id=None,
            )
            clusters[0].parent_id = new_cluster.id
            return [new_cluster, clusters[0]]

        self.sem = Semaphore(self.max_concurrent_requests)
        cluster_embeddings: list[list[float]] = await tqdm_asyncio.gather(
            *[
                self.embedding_model.embed(
                    f"""
Name: {cluster.name}
Description: {cluster.description}
                """.strip(),
                    self.sem,
                )
                for cluster in clusters
            ],
            desc="Embedding Clusters",
        )
        clusters_and_embeddings = [
            {
                "item": cluster,
                "embedding": embedding,
            }
            for cluster, embedding in zip(clusters, cluster_embeddings)
        ]

        cluster_id_to_clusters: dict[int, list[Cluster]] = (
            self.clustering_model.cluster(clusters_and_embeddings)
        )

        new_clusters = await tqdm_asyncio.gather(
            *[
                self.generate_meta_clusters(cluster_id_to_clusters[cluster_id])
                for cluster_id in cluster_id_to_clusters
            ],
            desc="Generating Meta Clusters",
        )

        res = []
        for new_cluster in new_clusters:
            res.extend(new_cluster)

        return res
