"""Text measurement and wrapping utilities.

Uses Pillow's ImageFont if available/font loaded, otherwise fallbacks to
proportional font character width metrics. Calculates wrapped line count
and required height in EMU or points.
"""
from __future__ import annotations

import re
from typing import Sequence

from PIL import ImageFont

from htmlppt import EMU_PER_PT
from htmlppt.analyze.ir import Run


# Average character width ratios relative to font size (in pt) for common fonts
APPROX_CHAR_WIDTH_RATIOS = {
    "default": 0.52,
    "mono": 0.60,
    "narrow": 0.45,
    "wide": 0.58,
}


def estimate_run_width_pt(text: str, font_family: str, font_size_pt: float, bold: bool = False) -> float:
    """Estimate string width in points."""
    ratio = APPROX_CHAR_WIDTH_RATIOS.get("mono" if "mono" in font_family.lower() else "default", 0.52)
    if bold:
        ratio *= 1.08
    # Count uppercase and wide letters as slightly wider
    w = 0.0
    for ch in text:
        if ch in "WMm@%#&":
            w += font_size_pt * ratio * 1.3
        elif ch in "ijl|!:,.' ":
            w += font_size_pt * ratio * 0.55
        elif ch.isupper():
            w += font_size_pt * ratio * 1.15
        else:
            w += font_size_pt * ratio
    return w


def wrap_text_to_lines(text: str, max_width_pt: float, font_family: str, font_size_pt: float, bold: bool = False) -> list[str]:
    """Break text into wrapped lines given a max width in points."""
    if not text:
        return [""]
    paragraphs = text.split("\n")
    all_lines: list[str] = []
    
    for p in paragraphs:
        if not p:
            all_lines.append("")
            continue
        words = p.split(" ")
        current_line = []
        current_w = 0.0
        space_w = estimate_run_width_pt(" ", font_family, font_size_pt, bold)
        
        for w in words:
            word_w = estimate_run_width_pt(w, font_family, font_size_pt, bold)
            needed = word_w if not current_line else current_w + space_w + word_w
            if needed <= max_width_pt or not current_line:
                current_line.append(w)
                current_w = needed
            else:
                all_lines.append(" ".join(current_line))
                current_line = [w]
                current_w = word_w
        if current_line:
            all_lines.append(" ".join(current_line))
            
    return all_lines


def estimate_text_height_emu(
    text: str,
    max_width_emu: int,
    font_family: str,
    font_size_pt: float,
    line_spacing: float = 1.2,
    bold: bool = False,
) -> int:
    """Calculate needed height in EMU for a block of text."""
    max_width_pt = max_width_emu / EMU_PER_PT
    lines = wrap_text_to_lines(text, max_width_pt, font_family, font_size_pt, bold)
    line_count = len(lines)
    height_pt = line_count * font_size_pt * line_spacing
    return int(height_pt * EMU_PER_PT)


def fit_font_size(
    text: str,
    max_width_emu: int,
    max_height_emu: int,
    font_family: str,
    preferred_size_pt: float,
    min_size_pt: float = 10.0,
    line_spacing: float = 1.2,
    bold: bool = False,
) -> float:
    """Auto-shrink font size between preferred_size_pt and min_size_pt to fit the bounding box."""
    size = preferred_size_pt
    while size >= min_size_pt:
        h = estimate_text_height_emu(text, max_width_emu, font_family, size, line_spacing, bold)
        if h <= max_height_emu:
            return size
        size -= 1.0
    return min_size_pt
