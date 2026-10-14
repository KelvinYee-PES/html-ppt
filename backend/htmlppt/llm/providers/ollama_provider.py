"""Optional local Ollama provider."""
from __future__ import annotations

import os
import urllib.request
from htmlppt.analyze import ir
from htmlppt.llm.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    @property
    def name(self) -> str:
        return "Ollama"

    def is_available(self) -> bool:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            req = urllib.request.urlopen(f"{host}/api/tags", timeout=1.0)
            return req.status == 200
        except Exception:
            return False

    def refine_deck(self, deck: ir.Deck) -> ir.Deck:
        if not self.is_available():
            return deck
        return deck
