from abc import ABC, abstractmethod
from ..normalization.normalizer import normalized_source
from ...schemas.analysis import AnalysisOutput

class AIUnavailable(Exception):
    pass

class AIProvider(ABC):
    @abstractmethod
    def analyze_sources(self, sources: list[dict]) -> AnalysisOutput:
        raise NotImplementedError
