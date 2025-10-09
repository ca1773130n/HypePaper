from abc import ABC, abstractmethod
from sotapapers.core.settings import Settings

import loguru
from pathlib import Path

class LLMClient(ABC):
    def __init__(self, settings: Settings, logger: loguru.logger):
        self.settings = settings
        self.logger = logger

    @abstractmethod
    def attach_file(self, file_path: Path) -> None:
        pass

    @abstractmethod
    def run(self, prompt: str) -> str:
        pass
