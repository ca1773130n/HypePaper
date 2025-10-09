from abc import ABC, abstractmethod
from typing import List

from sotapapers.core.paper import Paper

class PaperSearchClient(ABC):
    @abstractmethod
    def search(self, keyword: str) -> List[Paper]:
        pass

    @abstractmethod
    def search_by_title(self, title: str) -> Paper:
        pass