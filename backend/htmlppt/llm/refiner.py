"""Coordinates optional LLM refinement."""
from __future__ import annotations

import os
from htmlppt.analyze import ir
from htmlppt.llm.base import BaseLLMProvider
from htmlppt.llm.providers.gemini_provider import GeminiProvider
from htmlppt.llm.providers.ollama_provider import OllamaProvider
from htmlppt.llm.providers.openai_provider import OpenAIProvider


def get_available_provider() -> BaseLLMProvider | None:
    providers = [OpenAIProvider(), GeminiProvider(), OllamaProvider()]
    for p in providers:
        if p.is_available():
            return p
    return None


def maybe_refine_deck(deck: ir.Deck, enabled: bool = False) -> ir.Deck:
    """Run LLM refinement if explicitly enabled or requested in options."""
    if not enabled:
        return deck
    provider = get_available_provider()
    if not provider:
        return deck
    try:
        return provider.refine_deck(deck)
    except Exception:
        return deck
