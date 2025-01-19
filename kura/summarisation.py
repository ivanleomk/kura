from kura.base_classes import BaseSummaryModel
from kura.types import Conversation, ConversationSummary
from kura.types.summarisation import GeneratedSummary
from asyncio import Semaphore
from tqdm.asyncio import tqdm_asyncio
import google.generativeai as genai
import instructor
import os


class SummaryModel(BaseSummaryModel):
    def __init__(
        self,
        max_concurrent_requests: int = 50,
    ):
        self.sem = Semaphore(max_concurrent_requests)
        self.client = instructor.from_gemini(
            genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest",
            ),
            use_async=True,
        )

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
        self, conversation: ConversationSummary
    ) -> ConversationSummary:
        # TODO: Implement hooks here for extra metadata extraction
        return await super().apply_hooks(conversation)

    async def summarise_conversation(
        self, conversation: Conversation
    ) -> ConversationSummary:
        resp = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """
                    Generate a summary of the task that the user is asking the language model to do based off the following conversation.


                    The summary should be concise and short. It should be at most 1-2 sentences and at most 30 words. Here are some examples of summaries:
                    - The user’s overall request for the assistant is to help implementing a React component to display a paginated list of users from a database.
                    - The user’s overall request for the assistant is to debug a memory leak in their Python data processing pipeline.
                    - The user’s overall request for the assistant is to design and architect a REST API for a social media application.
                    

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
                }
            ],
            context={"messages": conversation.messages},
            response_model=GeneratedSummary,
        )
        return ConversationSummary(
            chat_id=conversation.chat_id,
            summary=resp.summary,
            metadata={
                "conversation_turns": len(conversation.messages),
            },
        )
