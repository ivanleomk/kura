from asyncio import Semaphore, gather
from typing import Any, Callable, Optional, Union

import instructor
from pydantic import BaseModel, Field
from tqdm.asyncio import tqdm_asyncio
import asyncio

from kura.base_classes import BaseSummaryModel
from kura.types import Conversation, ConversationSummary, ExtractedProperty
from kura.types.summarisation import GeneratedSummary

# Rich imports handled by Kura base class
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rich.console import Console



class GeneratedSummary(BaseModel):
    summary: str = Field(..., description="A clear and concise summary of the conversation in at most two sentences, avoiding phrases like 'Based on the conversation' and excluding proper nouns or PII")
    request: Optional[str] = Field(None, description="The user's overall request for the assistant")
    languages: Optional[list[str]] = Field(None, description="Main languages present in the conversation including human and programming languages (e.g., ['english', 'arabic', 'python', 'javascript'])")
    task: Optional[str] = Field(None, description="The task the model is being asked to perform")
    concerning_score: Optional[int] = Field(None, ge=1, le=5, description="Safety concern rating from 1-5 scale")
    user_frustration: Optional[int] = Field(None, ge=1, le=5, description="User frustration rating from 1-5 scale")
    assistant_errors: Optional[list[str]] = Field(None, description="List of errors the assistant made")
    

class ConversationSummary(GeneratedSummary):
    chat_id: str
    metadata: dict

class ExtractedProperty(BaseModel):
    name: str
    value: Union[str, int, float, bool, list[str], list[int], list[float]]


class SummaryModel(BaseSummaryModel):
    def __init__(
        self,
        model: str = "gemini/gemini-2.0-flash",
        max_concurrent_requests: int = 50,
        extractors: list[
            Callable[
                [Conversation, Semaphore, dict[str, Any]],
                dict,
            ]
        ] = [],
        console: Optional['Console'] = None,
        **kwargs, # For future use
    ):
        self.sems = None
        self.extractors = extractors
        self.max_concurrent_requests = max_concurrent_requests
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.console = console

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
                
                if show_preview:
                    # Use Live display with progress and preview buffer
                    layout = Layout()
                    layout.split_column(
                        Layout(name="progress", size=3),
                        Layout(name="preview")
                    )
                    
                    preview_buffer = []
                    max_preview_items = 3
                    
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
                                
                                # Add to preview buffer if it's a ConversationSummary
                                if hasattr(result, 'summary') and hasattr(result, 'chat_id'):
                                    preview_buffer.append(result)
                                    if len(preview_buffer) > max_preview_items:
                                        preview_buffer.pop(0)
                                    
                                    # Update preview display
                                    preview_text = Text()
                                    for j, summary in enumerate(preview_buffer):
                                        # Color based on user frustration level
                                        frustration_style = {
                                            1: "green",    # Not frustrated
                                            2: "yellow",   # Slightly frustrated
                                            3: "orange3",  # Moderately frustrated
                                            4: "red",      # Very frustrated
                                            5: "red1"      # Extremely frustrated
                                        }.get(summary.user_frustration, "white")

                                        # Color based on concerning score
                                        concern_style = {
                                            1: "green",    # Not concerning
                                            2: "yellow",   # Slightly concerning
                                            3: "orange3",  # Moderately concerning
                                            4: "red",      # Very concerning
                                            5: "red1"      # Extremely concerning
                                        }.get(summary.concerning_score, "white")

                                        preview_text.append(f"Chat {summary.chat_id[:8]}...: ", style="bold blue")
                                        preview_text.append(f"{summary.summary[:100]}...\n", style=frustration_style)
                                        
                                        if summary.request:
                                            preview_text.append(f"Request: {summary.request[:50]}...\n", style=frustration_style)
                                        if summary.languages:
                                            preview_text.append(f"Languages: {', '.join(summary.languages)}\n", style="dim cyan")
                                        if summary.task:
                                            preview_text.append(f"Task: {summary.task[:50]}...\n", style=concern_style)
                                        
                                        # Add frustration and concern indicators
                                        if summary.user_frustration:
                                            preview_text.append(f"Frustration: {'😊' * summary.user_frustration}\n", style=frustration_style)
                                        if summary.concerning_score:
                                            preview_text.append(f"Concern: {'⚠️' * summary.concerning_score}\n", style=concern_style)
                                        
                                        preview_text.append("\n")
                                    
                                    layout["preview"].update(Panel(
                                        preview_text,
                                        title=f"[green]Recent Summaries ({len(preview_buffer)}/{max_preview_items})",
                                        border_style="green"
                                    ))
                            
                            return completed_tasks
                    except LiveError:
                        # If Rich Live fails, fall back to simple progress without Live
                        with progress:
                            completed_tasks = []
                            for i, task in enumerate(asyncio.as_completed(tasks)):
                                result = await task
                                completed_tasks.append(result)
                                progress.update(task_id, completed=i + 1)
                            return completed_tasks
                else:
                    # Regular progress bar without preview
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
                # Rich not available or Live error, fall back to simple print statements
                self.console.print(f"[cyan]Starting {desc}...[/cyan]")
                completed_tasks = []
                for i, task in enumerate(asyncio.as_completed(tasks)):
                    result = await task
                    completed_tasks.append(result)
                    if (i + 1) % max(1, len(tasks) // 10) == 0 or i == len(tasks) - 1:
                        self.console.print(f"[cyan]{desc}: {i + 1}/{len(tasks)} completed[/cyan]")
                self.console.print(f"[green]✓ {desc} completed![/green]")
                return completed_tasks
        else:
            # Use tqdm as fallback when Rich is not available or disabled
            return await tqdm_asyncio.gather(*tasks, desc=desc, disable=disable)

    async def summarise(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
        # Initialise Semaphore if not already done
        if self.sems is None:
            self.sems = self.semaphore

        summaries = await self._gather_with_progress(
            [
                self.summarise_conversation(conversation)
                for conversation in conversations
            ],
            desc=f"Summarising {len(conversations)} conversations",
            show_preview=True,
        )
        return summaries

    async def apply_hooks(
        self, conversation: Conversation
    ) -> dict[str, Union[str, int, float, bool, list[str], list[int], list[float]]]:
        coros = [
            extractor(conversation, self.semaphore)
            for extractor in self.extractors
        ]
        metadata_extracted = await gather(*coros)  # pyright: ignore

        metadata = {}
        for result in metadata_extracted:
            if isinstance(result, ExtractedProperty):
                if result.name in metadata:
                    raise ValueError(
                        f"Duplicate metadata name: {result.name}. Please use unique names for each metadata property."
                    )

                metadata[result.name] = result.value

            if isinstance(result, list):
                for extracted_property in result:
                    assert isinstance(extracted_property, ExtractedProperty)
                    if extracted_property.name in metadata:
                        raise ValueError(
                            f"Duplicate metadata name: {extracted_property.name}. Please use unique names for each metadata property."
                        )
                    metadata[extracted_property.name] = extracted_property.value

        return metadata

    async def summarise_conversation(
        self, conversation: Conversation
    ) -> ConversationSummary:
        """
        This summarisation model is designed to extract key information from a conversation between an AI assistant and a user.
        It is designed to be used in a pipeline to summarise conversations and extract metadata.

        It is based on the Clio paper:
            https://assets.anthropic.com/m/7e1ab885d1b24176/original/Clio-Privacy-Preserving-Insights-into-Real-World-AI-Use.pdf

        It is designed to be used in a pipeline to summarise conversations and extract metadata.
        """
        client = instructor.from_provider(self.model, async_client=True)
        async with self.semaphore:  # type: ignore
            resp = await client.chat.completions.create(  # type: ignore
                temperature=0.2, # as per the Clio paper
                messages=[
                    {
                        "role": "user",
                        "content": """
                        Generate a summary of the task that the user is asking the language model to do based off the following conversation.


                        The summary should be concise and short. It should be at most 1-2 sentences and at most 30 words. Here are some examples of summaries:
                        - The user's overall request for the assistant is to help implementing a React component to display a paginated list of users from a database.
                        - The user's overall request for the assistant is to debug a memory leak in their Python data processing pipeline.
                        - The user's overall request for the assistant is to design and architect a REST API for a social media application.
                        """,
                    },
                    {
                        "role": "user",
                        "content": """
    Here is the conversation
    <messages>
    {% for message in messages %}
        <message>{{message.role}}: {{message.content}} </message>
    {% endfor %}
    </messages>

    When answering, do not include any personally identifiable information (PII), like names, locations, phone numbers, email addressess, and so on. When answering, do not include any proper nouns. Make sure that you're clear, concise and that you get to the point in at most two sentences.

    For example:

    Remember that
    - Summaries should be concise and short. They should each be at most 1-2 sentences and at most 30 words.
    - Summaries should start with "The user's overall request for the assistant is to"
    - Make sure to omit any personally identifiable information (PII), like names, locations, phone numbers, email addressess, company names and so on.
    - Make sure to indicate specific details such as programming languages, frameworks, libraries and so on which are relevant to the task.
                        """,
                    },
                ],
                context={"messages": conversation.messages},
                response_model=GeneratedSummary,
            )

        metadata = await self.apply_hooks(conversation)
        return ConversationSummary(
            chat_id=conversation.chat_id,
            summary=resp.summary,
            metadata={
                "conversation_turns": len(conversation.messages),
                **conversation.metadata,
                **metadata,
            },
        )
