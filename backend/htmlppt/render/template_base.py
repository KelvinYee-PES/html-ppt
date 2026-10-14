"""Presentation lifecycle and template management.

Creates blank presentation or opens an existing .pptx/.potx template,
clears existing slides while retaining slide masters and layouts.
"""
from __future__ import annotations

import io
from pathlib import Path
from pptx import Presentation
from pptx.presentation import Presentation as PresentationType
from pptx.slide import SlideLayout
from pptx.util import Emu

from htmlppt.brand.model import BrandProfile


def create_presentation(deck_width: int, deck_height: int, template_path: str | Path | None = None) -> PresentationType:
    """Create or load presentation and set target slide dimensions."""
    if template_path and Path(template_path).exists():
        prs = Presentation(str(template_path))
        # Clear existing slides in template (keeping masters and layouts)
        _clear_existing_slides(prs)
    else:
        prs = Presentation()

    prs.slide_width = Emu(deck_width)
    prs.slide_height = Emu(deck_height)
    return prs


def _clear_existing_slides(prs: PresentationType) -> None:
    """Remove all slides in presentation while preserving layouts and master slides."""
    r_ids = [s.slide_id for s in prs.slides]
    for r_id in r_ids:
        # python-pptx slide removal
        slide = prs.slides.get(slide_id=r_id)
        if slide:
            slide_idx = list(prs.slides).index(slide)
            rId = prs.slides._sldIdLst[slide_idx].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[slide_idx]


def select_slide_layout(prs: PresentationType, archetype: str) -> SlideLayout:
    """Select the best matching layout from presentation masters. Default to blank (idx 6)."""
    layouts = prs.slide_layouts
    archetype_lower = archetype.lower()

    # Try name-based matching
    for layout in layouts:
        name = (layout.name or "").lower()
        if archetype_lower in name:
            return layout
        if archetype_lower == "title" and "title" in name and "content" not in name:
            return layout
        if archetype_lower == "two_column" and ("two" in name or "comparison" in name):
            return layout
        if archetype_lower == "blank" and "blank" in name:
            return layout

    # Positional heuristics in standard Office templates:
    # 0: Title, 1: Title and Content, 2: Section Header, 3: Two Content, 6: Blank
    index_map = {
        "title": 0,
        "section": 2,
        "content": 1,
        "two_column": 3,
        "blank": 6,
    }
    target_idx = index_map.get(archetype_lower, 6)
    if target_idx < len(layouts):
        return layouts[target_idx]

    return layouts[len(layouts) - 1]  # fallback to last available
