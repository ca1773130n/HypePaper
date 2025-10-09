"""
LLM service abstraction supporting OpenAI and LlamaCpp.

Provides unified async interface for metadata extraction from PDFs
using either cloud-based (OpenAI) or local (LlamaCpp) LLM providers.
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp


class AsyncLLMService(ABC):
    """
    Abstract base class for async LLM services.

    Provides interface for extracting metadata from research papers
    using various LLM providers.
    """

    @abstractmethod
    async def extract_metadata(
        self,
        pdf_path: Path,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from PDF using LLM.

        Args:
            pdf_path: Path to PDF file
            prompt: Extraction prompt

        Returns:
            Dictionary with extracted metadata
        """
        pass

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed JSON as dictionary
        """
        # Remove markdown code blocks if present
        cleaned = response.strip()

        # Remove ```json ... ``` wrapper
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned = '\n'.join(lines)

        # Try to find JSON object or array
        json_match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # If parsing fails, return error info
            return {
                'error': 'Failed to parse JSON response',
                'raw_response': response[:500],  # First 500 chars
                'parse_error': str(e)
            }


class OpenAILLMService(AsyncLLMService):
    """
    OpenAI-based LLM service using Assistants API with file search.

    Supports GPT-4 and other OpenAI models with file upload capability.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        assistant_id: Optional[str] = None
    ):
        """
        Initialize OpenAI LLM service.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o)
            assistant_id: Pre-created assistant ID (optional)
        """
        self.api_key = api_key
        self.model = model
        self.assistant_id = assistant_id
        self.base_url = "https://api.openai.com/v1"

        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'OpenAI-Beta': 'assistants=v2'
        }

    async def extract_metadata(
        self,
        pdf_path: Path,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract metadata using OpenAI Assistants API with file search.

        Args:
            pdf_path: Path to PDF file
            prompt: Extraction prompt

        Returns:
            Extracted metadata as dictionary
        """
        async with aiohttp.ClientSession() as session:
            # Step 1: Upload file
            file_id = await self._upload_file(session, pdf_path)

            # Step 2: Create or use existing assistant
            if not self.assistant_id:
                self.assistant_id = await self._create_assistant(session)

            # Step 3: Create thread
            thread_id = await self._create_thread(session)

            # Step 4: Add message with file attachment
            await self._add_message(session, thread_id, prompt, file_id)

            # Step 5: Run assistant
            run_id = await self._create_run(session, thread_id)

            # Step 6: Wait for completion
            await self._wait_for_completion(session, thread_id, run_id)

            # Step 7: Get response
            response = await self._get_response(session, thread_id)

            # Parse JSON from response
            return self.parse_json_response(response)

    async def _upload_file(
        self,
        session: aiohttp.ClientSession,
        pdf_path: Path
    ) -> str:
        """Upload PDF to OpenAI."""
        data = aiohttp.FormData()
        data.add_field('purpose', 'assistants')
        data.add_field(
            'file',
            open(pdf_path, 'rb'),
            filename=pdf_path.name,
            content_type='application/pdf'
        )

        async with session.post(
            f"{self.base_url}/files",
            headers={'Authorization': self.headers['Authorization']},
            data=data
        ) as response:
            result = await response.json()
            return result['id']

    async def _create_assistant(self, session: aiohttp.ClientSession) -> str:
        """Create assistant with file search capability."""
        data = {
            'model': self.model,
            'name': 'Paper Metadata Extractor',
            'instructions': 'Extract metadata from research papers in JSON format.',
            'tools': [{'type': 'file_search'}]
        }

        async with session.post(
            f"{self.base_url}/assistants",
            headers=self.headers,
            json=data
        ) as response:
            result = await response.json()
            return result['id']

    async def _create_thread(self, session: aiohttp.ClientSession) -> str:
        """Create conversation thread."""
        async with session.post(
            f"{self.base_url}/threads",
            headers=self.headers,
            json={}
        ) as response:
            result = await response.json()
            return result['id']

    async def _add_message(
        self,
        session: aiohttp.ClientSession,
        thread_id: str,
        content: str,
        file_id: str
    ) -> None:
        """Add message to thread with file attachment."""
        data = {
            'role': 'user',
            'content': content,
            'attachments': [{
                'file_id': file_id,
                'tools': [{'type': 'file_search'}]
            }]
        }

        async with session.post(
            f"{self.base_url}/threads/{thread_id}/messages",
            headers=self.headers,
            json=data
        ) as response:
            await response.json()

    async def _create_run(
        self,
        session: aiohttp.ClientSession,
        thread_id: str
    ) -> str:
        """Start assistant run."""
        data = {
            'assistant_id': self.assistant_id
        }

        async with session.post(
            f"{self.base_url}/threads/{thread_id}/runs",
            headers=self.headers,
            json=data
        ) as response:
            result = await response.json()
            return result['id']

    async def _wait_for_completion(
        self,
        session: aiohttp.ClientSession,
        thread_id: str,
        run_id: str,
        timeout: int = 300
    ) -> None:
        """Poll until run completes."""
        start_time = asyncio.get_event_loop().time()

        while True:
            async with session.get(
                f"{self.base_url}/threads/{thread_id}/runs/{run_id}",
                headers=self.headers
            ) as response:
                result = await response.json()
                status = result['status']

                if status == 'completed':
                    return
                elif status in ['failed', 'cancelled', 'expired']:
                    raise Exception(f"Run {status}: {result.get('last_error')}")

                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError("Run timed out")

                await asyncio.sleep(2)

    async def _get_response(
        self,
        session: aiohttp.ClientSession,
        thread_id: str
    ) -> str:
        """Get assistant's response from thread."""
        async with session.get(
            f"{self.base_url}/threads/{thread_id}/messages",
            headers=self.headers
        ) as response:
            result = await response.json()
            messages = result['data']

            # Find first assistant message
            for message in messages:
                if message['role'] == 'assistant':
                    # Extract text from content
                    for content in message['content']:
                        if content['type'] == 'text':
                            return content['text']['value']

        return ''


class LlamaCppLLMService(AsyncLLMService):
    """
    Local LLM service using llama.cpp server.

    Connects to local llama.cpp server for inference without API costs.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:10002/v1/chat/completions",
        model: str = "Polaris-7B-preview"
    ):
        """
        Initialize LlamaCpp service.

        Args:
            server_url: URL of llama.cpp server
            model: Model name/identifier
        """
        self.server_url = server_url
        self.model = model

    async def extract_metadata(
        self,
        pdf_path: Path,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract metadata using local LLM.

        Args:
            pdf_path: Path to PDF file
            prompt: Extraction prompt

        Returns:
            Extracted metadata
        """
        # First extract text locally
        from .pdf_service import PDFAnalysisService
        pdf_service = PDFAnalysisService()
        full_text = await pdf_service.extract_text(pdf_path)

        # Truncate if too long (most models have token limits)
        max_chars = 12000  # Rough estimate for ~3000 tokens
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[...truncated...]"

        # Call local LLM server
        async with aiohttp.ClientSession() as session:
            data = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that extracts metadata from research papers. Always respond with valid JSON.'
                    },
                    {
                        'role': 'user',
                        'content': f"{prompt}\n\nPaper text:\n{full_text}"
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1000
            }

            async with session.post(
                self.server_url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                result = await response.json()

                if 'choices' in result and len(result['choices']) > 0:
                    message = result['choices'][0]['message']['content']
                    return self.parse_json_response(message)

        return {'error': 'Failed to get response from local LLM'}
