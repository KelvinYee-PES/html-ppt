"""API routes for Brand Profiles."""
from __future__ import annotations

import io
import tempfile
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from htmlppt.api._http import content_disposition
from htmlppt.brand.bundle import export_brand_bundle, import_brand_bundle
from htmlppt.brand.deck_analyzer import analyze_past_decks
from htmlppt.brand.model import BrandProfile
from htmlppt.brand.store import BrandStore
from htmlppt.brand.template_extractor import extract_brand_from_template

router = APIRouter(prefix="/api/brands", tags=["Brands"])
_store = BrandStore()


@router.get("", response_model=List[BrandProfile])
def list_brands():
    return _store.list_brands()


@router.get("/{brand_id}", response_model=BrandProfile)
def get_brand(brand_id: str):
    brand = _store.get_brand(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return brand


@router.post("", response_model=BrandProfile)
def save_brand(brand: BrandProfile):
    _store.save_brand(brand)
    return brand


@router.delete("/{brand_id}")
def delete_brand(brand_id: str):
    success = _store.delete_brand(brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return {"status": "deleted"}


@router.post("/extract-template", response_model=BrandProfile)
def extract_template(file: UploadFile = File(...)):
    """Upload a .potx or .pptx template to extract brand colors, fonts, slide size and layouts."""
    content = file.file.read()
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        brand = extract_brand_from_template(tmp_path, brand_name=Path(file.filename or "Template").stem)
        # Save template file into store
        file_id = f"tpl_{uuid.uuid4().hex[:8]}"
        _store.save_file(file_id, file.filename or "template.pptx", file.content_type or "application/vnd.openxmlformats-officedocument.presentationml.presentation", content)
        if brand.template:
            brand.template.file_id = file_id
            brand.template.filename = file.filename or "template.pptx"
        # Save brand to store
        _store.save_brand(brand)
        return brand
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


@router.post("/analyze-decks", response_model=BrandProfile)
def analyze_decks(files: List[UploadFile] = File(...)):
    """Upload one or more past .pptx decks to infer design language statistically."""
    tmp_paths: list[str] = []
    try:
        for f in files:
            content = f.file.read()
            with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                tmp.write(content)
                tmp_paths.append(tmp.name)

        brand = analyze_past_decks(tmp_paths)
        _store.save_brand(brand)
        return brand
    finally:
        for p in tmp_paths:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass


@router.get("/{brand_id}/export")
def export_brand(brand_id: str):
    brand = _store.get_brand(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    bundle_bytes = export_brand_bundle(brand, _store)
    return Response(
        content=bundle_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": content_disposition(f"{brand.name}.htmlppt-brand")},
    )


@router.post("/import", response_model=BrandProfile)
async def import_brand(file: UploadFile = File(...)):
    content = await file.read()
    try:
        brand = import_brand_bundle(content, _store)
        return brand
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import brand: {e}")
