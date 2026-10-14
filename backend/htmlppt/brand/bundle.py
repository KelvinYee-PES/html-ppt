"""Brand profile export/import bundle (.htmlppt-brand)."""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from htmlppt.brand.model import BrandProfile
from htmlppt.brand.store import BrandStore


def export_brand_bundle(brand: BrandProfile, store: BrandStore) -> bytes:
    """Pack a brand and its associated template/logo/font files into a zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Save brand.json
        zf.writestr("brand.json", brand.model_dump_json(indent=2))

        # Check and include referenced files
        file_ids_to_export = set()
        if brand.template and brand.template.file_id:
            file_ids_to_export.add(brand.template.file_id)
        if brand.logo and brand.logo.file_id:
            file_ids_to_export.add(brand.logo.file_id)
        if brand.fonts.heading.file_id:
            file_ids_to_export.add(brand.fonts.heading.file_id)
        if brand.fonts.body.file_id:
            file_ids_to_export.add(brand.fonts.body.file_id)

        for fid in file_ids_to_export:
            finfo = store.get_file(fid)
            if finfo:
                fname, ctype, fbytes = finfo
                zf.writestr(f"assets/{fid}/{fname}", fbytes)

    return buf.getvalue()


def import_brand_bundle(zip_bytes: bytes, store: BrandStore) -> BrandProfile:
    """Unpack a .htmlppt-brand bundle, save assets and register the brand profile."""
    buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buf, "r") as zf:
        if "brand.json" not in zf.namelist():
            raise ValueError("Invalid brand bundle: brand.json missing")

        brand_data = zf.read("brand.json").decode("utf-8")
        brand = BrandProfile.model_validate_json(brand_data)

        # Extract assets
        for item in zf.namelist():
            if item.startswith("assets/") and not item.endswith("/"):
                parts = item.split("/")
                if len(parts) >= 3:
                    file_id = parts[1]
                    filename = parts[2]
                    data = zf.read(item)
                    store.save_file(file_id, filename, "application/octet-stream", data)

        store.save_brand(brand)
        return brand
