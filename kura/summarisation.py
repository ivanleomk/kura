from kura.base_classes import BaseSummaryModel
from kura.types import Conversation, ConversationSummary, ExtractedProperty
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
        max_concurrent_requests: int = 50,
        client: instructor.AsyncInstructor = instructor.from_genai(
            Client(), use_async=True
        ),
        model: str = "gemini-2.0-flash",
        extractors: list[
            Callable[
                [Conversation, Semaphore, instructor.AsyncInstructor],
                dict,
            ]
        ] = [],
    ):
        self.max_concurrent_requests = max_concurrent_requests
        self.sem = None
        self.client = client
        self.model = model
        self.extractors = extractors

    async def summarise(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
        if self.sem is None:
            self.sem = asyncio.Semaphore(self.max_concurrent_requests)

        summaries = await tqdm_asyncio.gather(
            *[
                self.summarise_conversation(conversation)
                for conversation in conversations
            ],
            desc=f"Summarising {len(conversations)} conversations",
        )
        return summaries

    async def apply_hooks(self, conversation: Conversation) -> dict[str, any]:
        coros = [
            extractor(conversation, self.sem, self.client)
            for extractor in self.extractors
        ]
        results = await gather(*coros)
        return {result.name: result.value for result in results}

    async def summarise_conversation(
        self, conversation: Conversation
    ) -> ConversationSummary:
        resp = await self.client.chat.completions.create(
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
                **metadata,
            },
        )
