"""API routes for Conversion Jobs and Slide Manipulation."""
from __future__ import annotations

import io
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

from htmlppt.api._http import content_disposition
from htmlppt.analyze import ir
from htmlppt.analyze.segmenter import build_deck
from htmlppt.brand.model import BrandProfile
from htmlppt.brand.presets import apply_preset, palette_brand
from htmlppt.brand.store import BrandStore
from htmlppt.extract.renderer import snapshot_html
from htmlppt.layout import model as lm
from htmlppt.layout.engine import layout_deck
from htmlppt.layout.overflow import handle_overflow
from htmlppt.render.pptx_writer import write_pptx

router = APIRouter(prefix="/api/jobs", tags=["Conversion Jobs"])
_store = BrandStore()

# In-memory store for active conversion sessions
class JobState(BaseModel):
    id: str
    brand: BrandProfile
    preset: str
    dark: bool
    deck_ir: ir.Deck
    deck_model: lm.DeckModel
    template_path: Optional[str] = None

JOBS: dict[str, JobState] = {}


class SlideUpdateRequest(BaseModel):
    delete_indices: Optional[List[int]] = None
    reorder_indices: Optional[List[int]] = None
    layout_overrides: Optional[Dict[str, str]] = None  # slide_id -> archetype layout


@router.post("")
def create_job(
    html_file: Optional[UploadFile] = File(None),
    html_content: Optional[str] = Form(None),
    brand_id: Optional[str] = Form(None),
    palette: str = Form("ocean"),
    preset: str = Form("corporate"),
    dark: bool = Form(False),
):
    """Run conversion pipeline on provided HTML and return positioned slide models for preview."""
    # 1. Resolve HTML input
    if html_file:
        raw_bytes = html_file.file.read()
        html_str = raw_bytes.decode("utf-8", errors="replace")
    elif html_content:
        html_str = html_content
    else:
        raise HTTPException(status_code=400, detail="Either html_file or html_content must be provided")

    # 2. Resolve Brand & Preset
    template_path = None
    if brand_id:
        brand = _store.get_brand(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")
        # Check if template file exists in store
        if brand.template and brand.template.file_id:
            finfo = _store.get_file(brand.template.file_id)
            if finfo:
                _, _, tpl_bytes = finfo
                tmp_tpl = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
                tmp_tpl.write(tpl_bytes)
                tmp_tpl.close()
                template_path = tmp_tpl.name
    else:
        brand = palette_brand(palette_id=palette)

    brand = apply_preset(brand, preset_id=preset, dark=dark)

    # 3. Snapshot & Segment
    try:
        snap = snapshot_html(html=html_str)
        deck_ir = build_deck(snap)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse and segment HTML: {e}")

    # 4. Layout. Overflow splits are materialised into the IR first so that slide
    # indices in the returned deck model address the same slides in the IR.
    _expand_overflow(deck_ir, brand)
    deck_model = layout_deck(deck_ir, brand)

    # 5. Save job
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    JOBS[job_id] = JobState(
        id=job_id,
        brand=brand,
        preset=preset,
        dark=dark,
        deck_ir=deck_ir,
        deck_model=deck_model,
        template_path=template_path,
    )

    return {
        "job_id": job_id,
        "slide_count": len(deck_model.slides),
        "deck_model": deck_model,
        "warnings": deck_ir.warnings,
    }


@router.get("/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "slide_count": len(job.deck_model.slides),
        "deck_model": job.deck_model,
    }


@router.patch("/{job_id}/slides")
def update_slides(job_id: str, req: SlideUpdateRequest):
    """Reorder, delete, or override layouts of slides and recalculate layout.

    Indices refer to the slides of the deck model last returned to the client.
    A layout override of ``"auto"`` clears the override.
    """
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found. Convert the HTML again.")

    slides = list(job.deck_ir.slides)

    # Deletions
    if req.delete_indices:
        delete_set = set(req.delete_indices)
        if any(i < 0 or i >= len(slides) for i in delete_set):
            raise HTTPException(status_code=422, detail="delete_indices out of range")
        if len(delete_set) >= len(slides):
            raise HTTPException(status_code=422, detail="A deck needs at least one slide")
        slides = [s for i, s in enumerate(slides) if i not in delete_set]

    # Reorder
    if req.reorder_indices is not None:
        if sorted(req.reorder_indices) != list(range(len(slides))):
            raise HTTPException(status_code=422, detail="reorder_indices must be a permutation of slide indices")
        slides = [slides[i] for i in req.reorder_indices]

    # Layout overrides
    if req.layout_overrides:
        unknown = {v for v in req.layout_overrides.values() if v != "auto" and v not in LAYOUT_ARCHETYPES}
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown layout(s): {', '.join(sorted(unknown))}")
        for s in slides:
            if s.id in req.layout_overrides:
                layout = req.layout_overrides[s.id]
                s.layout = None if layout == "auto" else layout

    job.deck_ir.slides = slides
    # Re-run layout
    _expand_overflow(job.deck_ir, job.brand)
    job.deck_model = layout_deck(job.deck_ir, job.brand)

    return {
        "status": "updated",
        "slide_count": len(job.deck_model.slides),
        "deck_model": job.deck_model,
    }


@router.get("/{job_id}/pptx")
def download_pptx(job_id: str):
    """Compile and stream the generated PowerPoint file."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found. Convert the HTML again.")

    raw_bytes = write_pptx(job.deck_model, template_path=job.template_path)
    filename = f"{job.deck_ir.meta.title or 'Presentation'}.pptx".replace(" ", "_")

    return Response(
        content=raw_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": content_disposition(filename)},
    )


# ---------------------------------------------------------------- helpers

LAYOUT_ARCHETYPES = frozenset({
    "bullets", "two_column", "kpi_grid", "chart_focus", "chart_plus_text", "table",
    "cards", "quote", "title", "section", "closing", "freeform", "blank",
})


def _expand_overflow(deck_ir: ir.Deck, brand: BrandProfile) -> None:
    """Replace IR slides with their overflow-split parts (idempotent)."""
    expanded: list[ir.Slide] = []
    for s in deck_ir.slides:
        expanded.extend(handle_overflow(s, brand))
    deck_ir.slides = expanded
