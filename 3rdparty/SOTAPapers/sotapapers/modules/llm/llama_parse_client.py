from sotapapers.modules.llm_client import LLMClient
from sotapapers.core.settings import Settings

import os
import loguru

from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode

from copy import deepcopy
from pathlib import Path

class LlamaParseClient(LLMClient):
    def __init__(self, settings: Settings, logger: loguru.logger):
        super().__init__(settings, logger)
        os.environ["LLAMA_CLOUD_API_KEY"] = self.settings.external.llamaparse.api_key

    def attach_file(self, file_path: Path) -> None:
        self.documents = LlamaParse().load_data(file_path)
        self.nodes = self._get_page_nodes(self.documents)
        self.index = VectorStoreIndex(self.nodes)
        self.query_engine = self.index.as_query_engine(streaming=True, similarity_top_k=4)

    def run(self, prompt: str) -> str:
        response = self.query_engine.query(prompt)
        text = ''
        for text_chunk in response.response_gen:
            text += text_chunk
        return text
    
    def _get_page_nodes(self, docs, separator="\n---\n"):
        """Split each document into page node, by separator."""
        nodes = []
        for doc in docs:
            doc_chunks = doc.text.split(separator)
            for doc_chunk in doc_chunks:
                node = TextNode(
                    text=doc_chunk,
                    metadata=deepcopy(doc.metadata),
                )
                nodes.append(node)
        return nodes 