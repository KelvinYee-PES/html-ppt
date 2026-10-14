"""Optional OpenAI / Azure OpenAI provider."""
from __future__ import annotations

import os
from htmlppt.analyze import ir
from htmlppt.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    @property
    def name(self) -> str:
        return "OpenAI"

    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))

    def refine_deck(self, deck: ir.Deck) -> ir.Deck:
        if not self.is_available():
            return deck
        # Clean rule-based pass-through if no call made
        return deck
