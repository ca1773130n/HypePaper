from sotapapers.modules.llm_client import LLMClient
from sotapapers.core.settings import Settings

import loguru
from pathlib import Path

from openai import OpenAI
from openai.types.beta.threads.message_create_params import (
    Attachment,
    AttachmentToolFileSearch
)

class OpenAIClient(LLMClient):
    def __init__(self, settings: Settings, logger: loguru.logger):
        super().__init__(settings, logger)
        
        api_key = self.settings.external.openai.api_key
        client = OpenAI(api_key=api_key)

        self.openai_client = client
        self.pdf_assistant = client.beta.assistants.create(
            model="gpt-4o",
            description="An assistant to extract the contents of PDF files.",
            tools=[{"type": "file_search"}],
            name="PDF assistant",
        )

    def attach_file(self, file_path: Path) -> None:
        self.file = self.client.files.create(file=open(file_path, "rb"), purpose="assistants")

    def run(self, prompt: str) -> str:
        # Create thread
        thread = self.client.beta.threads.create()

        # Create assistant
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            attachments=[
                Attachment(
                    file_id=self.file.id, tools=[AttachmentToolFileSearch(type="file_search")]
                )
            ],
            content=prompt,
        )
        
        # Run thread
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=self.pdf_assistant.id, timeout=1000
        )

        if run.status != "completed":
            raise Exception("Run failed:", run.status)

        messages_cursor = self.client.beta.threads.messages.list(thread_id=thread.id)
        messages = [message for message in messages_cursor]

        # Output text
        content = messages[0].content[0]
        return content.text.value