from kura.base_classes import BaseSummaryModel
from kura.types import Conversation, ConversationSummary, ExtractedProperty
from typing import Union, Any
from kura.types.summarisation import GeneratedSummary
from asyncio import Semaphore, gather
from tqdm.asyncio import tqdm_asyncio
from google.genai import Client
import instructor
from typing import Callable
import asyncio


class SummaryModel(BaseSummaryModel):
    def __init__(
        self,
        concurrent_requests: dict[str, int] = {
            "default": 50,
        },
        clients: dict[str, Any] = {
            "default": instructor.from_genai(Client(), use_async=True)
        },
        model: str = "gemini-2.0-flash",
        extractors: list[
            Callable[
                [Conversation, dict[str, Semaphore], dict[str, Any]],
                dict,
            ]
        ] = [],
    ):
        self.sems = None
        self.model = model
        self.extractors = extractors
        self.concurrent_requests = concurrent_requests
        self.clients = clients

    async def summarise(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
        # Initialise Semaphores if not already done
        if not self.sems:
            sems = {}
            for (
                client_name,
                max_concurrent_requests,
            ) in self.concurrent_requests.items():
                sems[client_name] = asyncio.Semaphore(max_concurrent_requests)
            self.sems = sems

        assert "default" in self.sems, (
            "You must set a default semaphore for the main client"
        )
        assert "default" in self.clients, (
            "You must set a default client for the main client"
        )

        summaries = await tqdm_asyncio.gather(
            *[
                self.summarise_conversation(conversation)
                for conversation in conversations
            ],
            desc=f"Summarising {len(conversations)} conversations",
        )
        return summaries

    async def apply_hooks(
        self, conversation: Conversation
    ) -> dict[str, Union[str, int, float, bool, list[str], list[int], list[float]]]:
        assert self.sems is not None, (
            f"Semaphore is not set for {self.__class__.__name__}"
        )
        coros = [
            extractor(conversation, self.sems, self.clients)
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
        client = self.clients.get("default")  # type: ignore
        sem = self.sems.get("default")  # type: ignore

        assert client is not None and isinstance(client, instructor.AsyncInstructor), (
            "You must set a default client which uses the Async Instructor API"
        )
        assert sem is not None, "You must set a default semaphore"

        async with sem:  # type: ignore
            resp = await client.chat.completions.create(  # type: ignore
                model=self.model,
                messages=[
                    {
                        "role": "system",
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
