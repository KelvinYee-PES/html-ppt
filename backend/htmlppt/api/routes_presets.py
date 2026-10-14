"""API routes for style presets and palettes."""
from __future__ import annotations

from fastapi import APIRouter
from htmlppt.brand.presets import list_palettes, list_presets

router = APIRouter(prefix="/api", tags=["Presets & Palettes"])


@router.get("/presets")
def get_presets():
    return list_presets()


@router.get("/palettes")
def get_palettes():
    return list_palettes()
