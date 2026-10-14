"""Optional Google Gemini provider."""
from __future__ import annotations

import os
from htmlppt.analyze import ir
from htmlppt.llm.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    @property
    def name(self) -> str:
        return "Gemini"

    def is_available(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    def refine_deck(self, deck: ir.Deck) -> ir.Deck:
        if not self.is_available():
            return deck
        return deck
