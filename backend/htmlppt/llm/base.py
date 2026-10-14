"""Base LLM interface for optional slide refinement."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from htmlppt.analyze import ir


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if credentials/endpoints are configured."""
        ...

    @abstractmethod
    def refine_deck(self, deck: ir.Deck) -> ir.Deck:
        """Optionally improve action titles, classify ambiguous blocks, or condense text."""
        ...
