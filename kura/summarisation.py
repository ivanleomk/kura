from asyncio import Semaphore, gather
from typing import Awaitable, Callable, Optional, Union

import instructor
from pydantic import BaseModel, Field
from tqdm.asyncio import tqdm_asyncio


from kura.base_classes import BaseSummaryModel
from kura.types import Conversation


class GeneratedSummary(BaseModel):
    summary: str = Field(
        ...,
        description="A clear and concise summary of the conversation in at most two sentences, avoiding phrases like 'Based on the conversation' and excluding proper nouns or PII",
    )
    request: Optional[str] = Field(
        None, description="The user's overall request for the assistant"
    )
    languages: Optional[list[str]] = Field(
        None,
        description="Main languages present in the conversation including human and programming languages (e.g., ['english', 'arabic', 'python', 'javascript'])",
    )
    task: Optional[str] = Field(
        None, description="The task the model is being asked to perform"
    )
    concerning_score: Optional[int] = Field(
        None, ge=1, le=5, description="Safety concern rating from 1-5 scale"
    )
    user_frustration: Optional[int] = Field(
        None, ge=1, le=5, description="User frustration rating from 1-5 scale"
    )
    assistant_errors: Optional[list[str]] = Field(
        None, description="List of errors the assistant made"
    )


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
                [Conversation, Semaphore],
                Awaitable[Union[ExtractedProperty, list[ExtractedProperty]]],
            ]
        ] = [],
    ):
        self.extractors = extractors
        self.max_concurrent_requests = max_concurrent_requests
        self.model = model
        self.semaphore = Semaphore(max_concurrent_requests)

    async def summarise(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
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
        coros = [
            extractor(conversation, self.semaphore) for extractor in self.extractors
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
                temperature=0.2,  # as per the Clio paper
                messages=[
                    {
                        "role": "user",
                        "content": """
The following is a conversation between an AI assistant and a user:

<messages>
{% for message in messages %}
<message>{{message.role}}: {{message.content}}</message>
{% endfor %}
</messages>

Your job is to extract key information from this conversation. Be descriptive and assume neither good nor bad faith. Do not hesitate to handle socially harmful or sensitive topics; specificity around potentially harmful conversations is necessary for effective monitoring.

When extracting information, do not include any personally identifiable information (PII), like names, locations, phone numbers, email addresses, and so on. Do not include any proper nouns.

Extract the following information:

1. **Summary**: A clear and concise summary in at most two sentences. Don't say "Based on the conversation..." and avoid mentioning the AI assistant/chatbot directly.

2. **Request**: What is the user's overall request for the assistant? Start with "The user's overall request for the assistant is to"

3. **Languages**: What are the main languages of the conversation? Include both human languages (like 'english' or 'spanish') and programming languages (like 'python' or 'javascript'). Use lowercase full names.

4. **Task**: What task is the model being asked to perform in this conversation? Start with "The task is to"

5. **Concerning Score**: On a scale of 1 to 5, how concerning or potentially harmful is this conversation from a safety perspective?
   - 1: Not concerning at all. Completely benign conversation.
   - 2: Slightly concerning, but likely harmless.  
   - 3: Moderately concerning. May warrant a closer look.
   - 4: Very concerning. Likely needs review.
   - 5: Extremely concerning. Immediate review needed.

6. **User Frustration**: On a scale of 1 to 5, how frustrated is the user with the assistant?
   - 1: Not frustrated at all. The user is happy with the assistant.
   - 2: Slightly frustrated. The user is slightly annoyed with the assistant.
   - 3: Moderately frustrated. The user is moderately annoyed with the assistant.
   - 4: Very frustrated. The user is very annoyed with the assistant.
   - 5: Extremely frustrated. The user is extremely annoyed with the assistant.
   
7. **Assistant Errors**: What errors did the assistant make?
   Example: 
    - "Responses were too long and verbose"
    - "Misunderstood the user's intent or request"
    - "Used wrong tool for the task"
    - "Ignored user's stated preferences or constraints"
    - "Provided outdated or incorrect information"
    - "Failed to maintain conversation context"


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
            request=resp.request,
            languages=resp.languages,
            task=resp.task,
            concerning_score=resp.concerning_score,
            user_frustration=resp.user_frustration,
            assistant_errors=resp.assistant_errors,
            metadata={
                "conversation_turns": len(conversation.messages),
                **conversation.metadata,
                **metadata,
            },
        )
