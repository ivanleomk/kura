from kura.base_classes import BaseClusterModel, BaseClusteringMethod, BaseEmbeddingModel
from kura.embedding import OpenAIEmbeddingModel
from kura.k_means import KmeansClusteringMethod
from kura.types import ConversationSummary, Cluster, GeneratedCluster
from tqdm.asyncio import tqdm_asyncio
import numpy as np
from asyncio import Semaphore
import instructor
import asyncio

# Rich imports handled by Kura base class
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from rich.console import Console


class ClusterModel(BaseClusterModel):
    def __init__(
        self,
        clustering_method: BaseClusteringMethod = KmeansClusteringMethod(),
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
        max_concurrent_requests: int = 50,
        model: str = "openai/gpt-4o",
        console: Optional['Console'] = None,
        **kwargs, # For future use
    ):
        self.clustering_method = clustering_method
        self.embedding_model = embedding_model
        self.max_concurrent_requests = max_concurrent_requests
        self.client = instructor.from_provider(model, async_client=True)
        self.console = console

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
                messages=[
                    {
                        "role": "system",
                        "content": """
You are tasked with summarizing a group of related statements into a short, precise, and accurate description and name. Your goal is to create a concise summary that captures the essence of these statements and distinguishes them from other similar groups of statements.

Summarize all the statements into a clear, precise, two-sentence description in the past tense. Your summary should be specific to this group and distinguish it from the contrastive answers of the other groups.

After creating the summary, generate a short name for the group of statements. This name should be at most ten words long (perhaps less) and be specific but also reflective of most of the statements (rather than reflecting only one or two).

The name should distinguish this group from the contrastive examples. For instance, "Write fantasy sexual roleplay with octopi and monsters", "Generate blog spam for gambling websites", or "Assist with high school math homework" would be better and more actionable than general terms like "Write erotic content" or "Help with homework". Be as descriptive as possible and assume neither good nor bad faith. Do not hesitate to identify and describe socially harmful or sensitive topics specifically; specificity is necessary for monitoring.

Present your output in the following format:
<summary> [Insert your two-sentence summary here] </summary>
<name> [Insert your generated short name here] </name>

The names you propose must follow these requirements:
- The cluster name should be a sentence in the imperative that captures the user's request. For example, 'Brainstorm ideas for a birthday party' or 'Help me find a new job.'
- Create names that are specific enough to be meaningful, but not so specific that they can't meaningfully represent many different statements.
- Avoid overly general or vague terms, and do not hesitate to describe socially harmful or sensitive topics (in fact, clusters that clearly describe harmful behavior are slightly preferred); specificity is necessary for observability and enforcement.
- Ensure that the cluster name is distinct from the contrastive examples.
- Use clear, concise, and descriptive language for the cluster name.

Below are the related statements:
<positive_examples>
{% for item in positive_examples %}{{ item.summary }}
{% endfor %}
</positive_examples>

For context, here are statements from nearby groups that are NOT part of the group you're summarizing:
<contrastive_examples>
{% for item in contrastive_examples %}{{ item.summary }}
{% endfor %}
</contrastive_examples>

Do not elaborate beyond what you say in the tags. Remember to analyze both the statements and the contrastive statements carefully to ensure your summary and name accurately represent the specific group while distinguishing it from others.
                    """,
                    },
                    {
                        "role": "user", 
                        "content": "The cluster name should be a sentence in the imperative that captures the user's request. For example, 'Brainstorm ideas for a birthday party' or 'Help me find a new job.'"
                    },
                    {
                        "role": "assistant",
                        "content": "Sure, I will provide a clear, precise, and accurate summary and name for this cluster. I will be descriptive and assume neither good nor bad faith. Here is the summary, which I will follow with the name:"
                    }
                ],
                response_model=GeneratedCluster,
                context={
                    "positive_examples": summaries,
                    "contrastive_examples": contrastive_examples,
                },
            )

            return Cluster(
                name=resp.name,
                description=resp.summary,
                chat_ids=[item.chat_id for item in summaries],
                parent_id=None,
            )

    async def cluster_summaries(
        self, summaries: list[ConversationSummary]
    ) -> list[Cluster]:
        sem = Semaphore(self.max_concurrent_requests)
        embeddings: list[list[float]] = await self._gather_with_progress(
            [
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
        clusters: list[Cluster] = await self._gather_with_progress(
            [
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
            show_preview=True,
        )

        return clusters

    async def _gather_with_progress(self, tasks, desc: str = "Processing", disable: bool = False, show_preview: bool = False):
        """Helper method to run async gather with Rich progress bar if available, otherwise tqdm."""
        if self.console and not disable:
            try:
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
                from rich.live import Live
                from rich.layout import Layout
                from rich.panel import Panel
                from rich.text import Text
                from rich.errors import LiveError
            except ImportError:
                return await tqdm_asyncio.gather(*tasks, desc=desc, disable=disable)
                
            if show_preview:
                # Use Live display with progress and cluster list
                layout = Layout()
                layout.split_column(
                    Layout(name="progress", size=3),
                    Layout(name="clusters")
                )
                
                all_clusters = []
                
                # Create progress with cleaner display
                progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    console=self.console
                )
                task_id = progress.add_task(f"[cyan]{desc}...", total=len(tasks))
                layout["progress"].update(progress)
                
                try:
                    with Live(layout, console=self.console, refresh_per_second=4) as live:
                        completed_tasks = []
                        for i, task in enumerate(asyncio.as_completed(tasks)):
                            result = await task
                            completed_tasks.append(result)
                            progress.update(task_id, completed=i + 1)
                            
                            # Add to cluster list if it's a Cluster
                            if hasattr(result, 'name') and hasattr(result, 'description'):
                                all_clusters.append(result)
                                
                                # Sort clusters by conversation count (largest first)
                                sorted_clusters = sorted(all_clusters, key=lambda x: len(x.chat_ids), reverse=True)
                                
                                # Create formatted list display
                                cluster_text = Text()
                                for j, cluster in enumerate(sorted_clusters):
                                    cluster_text.append(f"#{j+1} ", style="bold cyan")
                                    cluster_text.append(f"{cluster.name}\n", style="bold white")
                                    cluster_text.append(f"    {cluster.description[:120]}...\n", style="dim white")
                                    cluster_text.append(f"    💬 {len(cluster.chat_ids)} conversations\n\n", style="dim cyan")
                                
                                layout["clusters"].update(Panel(
                                    cluster_text,
                                    title=f"[green]Generated Clusters ({len(all_clusters)}) - Sorted by Size",
                                    border_style="green"
                                ))
                        
                        return completed_tasks
                except LiveError:
                    # If Rich Live fails, run silently
                    return await asyncio.gather(*tasks)
            else:
                # Regular progress bar without preview
                try:
                    progress = Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TaskProgressColumn(),
                        TimeRemainingColumn(),
                        console=self.console
                    )
                    
                    with progress:
                        task_id = progress.add_task(f"[cyan]{desc}...", total=len(tasks))
                        
                        completed_tasks = []
                        for i, task in enumerate(asyncio.as_completed(tasks)):
                            result = await task
                            completed_tasks.append(result)
                            progress.update(task_id, completed=i + 1)
                        
                        return completed_tasks
                except (ImportError, LiveError) as e:
                    # Rich not available or Live error, run silently
                    return await asyncio.gather(*tasks)
        else:
            # No console, run silently
            return await asyncio.gather(*tasks)
