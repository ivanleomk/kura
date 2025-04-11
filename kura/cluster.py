from kura.base_classes import BaseClusterModel, BaseClusteringMethod, BaseEmbeddingModel
from kura.embedding import OpenAIEmbeddingModel
from kura.k_means import KmeansClusteringMethod
from kura.metadata import combine_summary_metadata
from kura.types import ConversationSummary, Cluster, GeneratedCluster
from tqdm.asyncio import tqdm_asyncio
import numpy as np
from asyncio import Semaphore
import instructor
from google.genai import Client


class ClusterModel(BaseClusterModel):
    def __init__(
        self,
        clustering_method: BaseClusteringMethod = KmeansClusteringMethod(),
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
        max_concurrent_requests: int = 50,
        client=instructor.from_genai(Client(), use_async=True),
        model="gemini-2.0-flash",
    ):
        self.clustering_method = clustering_method
        self.embedding_model = embedding_model
        self.max_concurrent_requests = max_concurrent_requests
        self.client = client
        self.model = model

    def get_contrastive_examples(
        self,
        cluster_id: int,
        cluster_id_to_summaries: dict[int, list[ConversationSummary]],
        desired_count: int = 10,
    ):
        other_clusters = [c for c in cluster_id_to_summaries.keys() if c != cluster_id]
        all_examples = []
        for cluster in other_clusters:
            all_examples.extend(cluster_id_to_summaries[cluster])

        # If we don't have enough examples, return all of them
        if len(all_examples) <= desired_count:
            return all_examples

        # Otherwise sample without replacement
        return list(np.random.choice(all_examples, size=desired_count, replace=False))

    async def generate_cluster(
        self,
        summaries: list[ConversationSummary],
        contrastive_examples: list[ConversationSummary],
        sem: Semaphore,
    ) -> Cluster:
        async with sem:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
                    You are tasked with summarizing a group of related statements into a short, precise, and accurate description and name. Your goal is to create a concise summary that captures the essence of these statements and distinguishes them from other similar groups of statements.
                    
                    Summarize all the statements into a clear, precise, two-sentence description in the past tense. Your summary should be specific to this group and distinguish it from the contrastive answers of the other groups.

                    After creating the summary, generate a short name for the group of statements. This name should be at most ten words long (perhaps less) and be specific but also reflective of most of the statements (rather than reflecting only one or two). The name should distinguish this group from the contrastive examples. For instance, "Write fantasy sexual roleplay with octopi and monsters", "Generate blog spam for gambling websites", or "Assist with high school math homework" would be better and more actionable than general terms like "Write erotic content" or "Help with homework". Be as descriptive as possible and assume neither good nor bad faith. Do not hesitate to identify and describe socially harmful or sensitive topics specifically; specificity is necessary for monitoring
                    
                    The cluster name should be a sentence in the imperative that captures the user’s request. For example, ‘Brainstorm ideas for a birthday party’ or ‘Help me find a new job.”
                    """,
                    },
                    {
                        "role": "user",
                        "content": """
                    Here are the relevant statements

                    Below are the related statements:
                    <positive_examples>
                    {% for item in positive_examples %}
                        <positive_example>{{ item.summary }}</positive_example>
                    {% endfor %}
                    </positive_examples>  
                    
                    For context, here are statements from nearby groups that are NOT part of the group you’re summarizing
                    
                    <contrastive_examples>
                    {% for item in contrastive_examples %}
                    <contrastive_example>{{ item.summary }}</contrastive_example>
                    {% endfor %}
                    </contrastive_examples>
                    
                    Remember to analyze both the statements and the contrastive statements carefully to ensure your summary and name accurately represent the specific group while distinguishing it from others.
                    """,
                    },
                ],
                response_model=GeneratedCluster,
                context={
                    "positive_examples": summaries,
                    "contrastive_examples": contrastive_examples,
                },
            )

            combined_metadata = combine_summary_metadata(
                [item.metadata for item in summaries]
            )

            return Cluster(
                name=resp.name,
                description=resp.summary,
                chat_ids=[item.chat_id for item in summaries],
                parent_id=None,
                metadata=combined_metadata,
            )

    async def cluster_summaries(
        self, summaries: list[ConversationSummary]
    ) -> list[Cluster]:
        sem = Semaphore(self.max_concurrent_requests)
        embeddings: list[list[float]] = await tqdm_asyncio.gather(
            *[
                self.embedding_model.embed(text=item.summary, sem=sem)
                for item in summaries
            ],
            desc="Embedding Summaries",
        )
        cluster_id_to_summaries = self.clustering_method.cluster(
            [
                {
                    "item": item,
                    "embedding": embedding,
                }
                for item, embedding in zip(summaries, embeddings)
            ]
        )
        clusters: list[Cluster] = await tqdm_asyncio.gather(
            *[
                self.generate_cluster(
                    summaries,
                    self.get_contrastive_examples(
                        cluster_id, cluster_id_to_summaries, 10
                    ),
                    sem,
                )
                for cluster_id, summaries in cluster_id_to_summaries.items()
            ],
            desc="Generating Base Clusters",
        )

        return clusters
