"""Extract brand information from a PowerPoint template (.potx / .pptx).

Reads OOXML parts directly via zipfile & lxml:
- Theme colors from `ppt/theme/theme1.xml` (clrScheme: dk1, lt1, dk2, lt2, accent1-6, hlink)
- Major/minor fonts from `ppt/theme/theme1.xml` (fontScheme)
- Masters and slide layouts with their placeholder geometry and types
- Master slide background fills and logo images
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree

from htmlppt import EMU_PER_INCH
from htmlppt.brand.model import (
    BrandProfile,
    ColorRoles,
    DesignLanguage,
    FontSizes,
    FontSpec,
    Fonts,
    Logo,
    SlideSize,
    SourceInfo,
    TemplateRef,
    ThemeColors,
)

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

NAMESPACES = {"a": A_NS, "p": P_NS, "r": R_NS}


def extract_brand_from_template(file_path: str | Path, brand_name: str | None = None) -> BrandProfile:
    """Extract theme colors, fonts, dimensions and layout map from a .pptx/.potx file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Template file {path} not found")

    brand = BrandProfile(name=brand_name or path.stem, organization="Custom")
    source_info = SourceInfo(kind="template", filename=path.name, notes="Extracted from template")

    with zipfile.ZipFile(path, "r") as zf:
        # 1. Slide Size
        _extract_presentation_props(zf, brand)

        # 2. Theme Colors & Fonts
        _extract_theme(zf, brand, source_info)

        # 3. Slide Layouts
        layout_summary, layout_map = _extract_layouts(zf, brand)
        brand.template = TemplateRef(
            file_id=path.name,
            filename=path.name,
            layout_map=layout_map,
            layouts=layout_summary,
        )

        # 4. Master Slide Logos / Graphics
        _extract_master_elements(zf, brand)

    brand.derive_roles_from_theme()
    brand.sources.append(source_info)
    return brand


def _extract_presentation_props(zf: zipfile.ZipFile, brand: BrandProfile) -> None:
    if "ppt/presentation.xml" not in zf.namelist():
        return
    tree = etree.fromstring(zf.read("ppt/presentation.xml"))
    sldSz = tree.find(".//p:sldSz", NAMESPACES)
    if sldSz is not None:
        cx = int(sldSz.get("cx", 13.333 * EMU_PER_INCH))
        cy = int(sldSz.get("cy", 7.5 * EMU_PER_INCH))
        brand.slide_size = SlideSize(width=cx, height=cy)


def _extract_theme(zf: zipfile.ZipFile, brand: BrandProfile, source: SourceInfo) -> None:
    theme_files = [f for f in zf.namelist() if f.startswith("ppt/theme/theme") and f.endswith(".xml")]
    if not theme_files:
        return
    tree = etree.fromstring(zf.read(theme_files[0]))

    # Color scheme
    clrScheme = tree.find(".//a:clrScheme", NAMESPACES)
    if clrScheme is not None:
        colors_dict = {}
        for child in clrScheme:
            tag = etree.QName(child).localname
            srgb = child.find(".//a:srgbClr", NAMESPACES)
            sysClr = child.find(".//a:sysClr", NAMESPACES)
            hex_val = None
            if srgb is not None:
                hex_val = srgb.get("val")
            elif sysClr is not None:
                hex_val = sysClr.get("lastClr", "000000")

            if hex_val and len(hex_val) == 6:
                colors_dict[tag] = hex_val.upper()

        brand.colors = ThemeColors(**{k: v for k, v in colors_dict.items() if hasattr(ThemeColors, k)})
        source.confidence["colors"] = 1.0

    # Font scheme
    fontScheme = tree.find(".//a:fontScheme", NAMESPACES)
    if fontScheme is not None:
        major = fontScheme.find(".//a:majorFont/a:latin", NAMESPACES)
        minor = fontScheme.find(".//a:minorFont/a:latin", NAMESPACES)
        if major is not None and major.get("typeface"):
            brand.fonts.heading.family = major.get("typeface")
        if minor is not None and minor.get("typeface"):
            brand.fonts.body.family = minor.get("typeface")
        source.confidence["fonts"] = 1.0


def _extract_layouts(zf: zipfile.ZipFile, brand: BrandProfile) -> tuple[list[dict], dict[str, str]]:
    """Inspect slideLayout*.xml files to find available layout names and map archetypes."""
    layout_files = [f for f in zf.namelist() if re.match(r"^ppt/slideLayouts/slideLayout\d+\.xml$", f)]
    layouts_info: list[dict] = []
    layout_map: dict[str, str] = {}

    for lf in sorted(layout_files):
        tree = etree.fromstring(zf.read(lf))
        # Layout name attribute: p:cSld/@name
        cSld = tree.find("p:cSld", NAMESPACES)
        name = cSld.get("name", Path(lf).stem) if cSld is not None else Path(lf).stem

        # Placeholders
        phs = []
        for sp in tree.findall(".//p:sp", NAMESPACES):
            ph = sp.find(".//p:nvPr/p:ph", NAMESPACES)
            if ph is not None:
                ph_type = ph.get("type", "body")
                ph_idx = ph.get("idx", "0")
                phs.append({"type": ph_type, "idx": ph_idx})

        layouts_info.append({"file": lf, "name": name, "placeholders": phs})

        # Map archetypes
        lname = name.lower()
        if "title" in lname and "content" not in lname and "title" not in layout_map:
            layout_map["title"] = name
        elif ("two" in lname or "comparison" in lname) and "two_content" not in layout_map:
            layout_map["two_content"] = name
        elif "section" in lname and "section" not in layout_map:
            layout_map["section"] = name
        elif "blank" in lname and "blank" not in layout_map:
            layout_map["blank"] = name
        elif ("title only" in lname or "title_only" in lname) and "title_only" not in layout_map:
            layout_map["title_only"] = name
        elif ("content" in lname or "title and content" in lname) and "content" not in layout_map:
            layout_map["content"] = name

    # Defaults if missing
    if "content" not in layout_map and layouts_info:
        layout_map["content"] = layouts_info[0]["name"]

    return layouts_info, layout_map


def _extract_master_elements(zf: zipfile.ZipFile, brand: BrandProfile) -> None:
    """Find images placed on slideMaster1 (often corporate logos)."""
    master_files = [f for f in zf.namelist() if f.startswith("ppt/slideMasters/slideMaster") and f.endswith(".xml")]
    if not master_files:
        return

    tree = etree.fromstring(zf.read(master_files[0]))
    # Look for pic elements
    for pic in tree.findall(".//p:pic", NAMESPACES):
        blip = pic.find(".//a:blip", NAMESPACES)
        xfrm = pic.find(".//p:spPr/a:xfrm", NAMESPACES)
        if blip is not None and xfrm is not None:
            off = xfrm.find("a:off", NAMESPACES)
            ext = xfrm.find("a:ext", NAMESPACES)
            if off is not None and ext is not None:
                cx = int(ext.get("cx", 0))
                cy = int(ext.get("cy", 0))
                # Reasonable logo dimensions: width between 0.5" and 3.0"
                if 0.5 * EMU_PER_INCH <= cx <= 3.5 * EMU_PER_INCH:
                    brand.logo = Logo(
                        file_id="master_logo",
                        position="top-right",
                        width=cx,
                        from_template=True,
                    )
                    break
