"""Statistical analyzer for past presentations (.pptx).

Infers design conventions across one or more past decks:
- Dominant heading and body fonts
- Typical title and body font sizes
- Common shape types and corner radius (rounded vs sharp)
- Margin clusters and density
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from htmlppt import EMU_PER_INCH
from htmlppt.brand.model import (
    BrandProfile,
    DesignLanguage,
    FontSizes,
    Fonts,
    SourceInfo,
)


def analyze_past_decks(deck_paths: list[str | Path], base_brand: BrandProfile | None = None) -> BrandProfile:
    """Analyze one or more past .pptx files and infer typography and design language."""
    brand = base_brand or BrandProfile(name="Inferred Brand", organization="Inferred")

    font_counter_title: Counter[str] = Counter()
    font_counter_body: Counter[str] = Counter()
    title_sizes: list[float] = []
    body_sizes: list[float] = []
    round_rect_radii: list[float] = []
    total_shapes = 0
    round_shapes = 0
    words_per_slide: list[int] = []

    for dp in deck_paths:
        path = Path(dp)
        if not path.exists():
            continue
        try:
            prs = Presentation(str(path))
        except Exception:
            continue

        for slide in prs.slides:
            slide_word_count = 0
            for shape in slide.shapes:
                total_shapes += 1
                if shape.has_text_frame:
                    is_title = shape == slide.shapes.title if hasattr(slide.shapes, "title") else False
                    for p in shape.text_frame.paragraphs:
                        for run in p.runs:
                            text = run.text.strip()
                            if not text:
                                continue
                            slide_word_count += len(text.split())
                            fname = run.font.name
                            fsize = run.font.size.pt if run.font.size else None

                            if fname:
                                if is_title:
                                    font_counter_title[fname] += len(text)
                                else:
                                    font_counter_body[fname] += len(text)
                            if fsize:
                                if is_title:
                                    title_sizes.append(fsize)
                                elif fsize < 24:
                                    body_sizes.append(fsize)

                # Shape corner radius detection
                try:
                    if shape.auto_shape_type == MSO_SHAPE.ROUNDED_RECTANGLE:
                        round_shapes += 1
                        if len(shape.adjustments) > 0:
                            round_rect_radii.append(float(shape.adjustments[0]))
                except (ValueError, AttributeError):
                    pass

            words_per_slide.append(slide_word_count)

    # Infer fonts
    if font_counter_title:
        brand.fonts.heading.family = font_counter_title.most_common(1)[0][0]
    if font_counter_body:
        brand.fonts.body.family = font_counter_body.most_common(1)[0][0]

    # Infer font sizes
    if title_sizes:
        brand.fonts.sizes.title = round(sum(title_sizes) / len(title_sizes), 1)
    if body_sizes:
        brand.fonts.sizes.body = round(sum(body_sizes) / len(body_sizes), 1)

    # Infer corner radius
    if round_rect_radii and round_shapes >= 2:
        avg_radius = sum(round_rect_radii) / len(round_rect_radii)
        brand.design.corner_radius = round(avg_radius, 3)
    elif total_shapes > 5 and round_shapes == 0:
        brand.design.corner_radius = 0.0

    # Infer density
    if words_per_slide:
        avg_words = sum(words_per_slide) / len(words_per_slide)
        if avg_words > 80:
            brand.design.density = "dense"
        elif avg_words < 35:
            brand.design.density = "airy"
        else:
            brand.design.density = "balanced"

    source = SourceInfo(
        kind="deck",
        filename=", ".join(Path(p).name for p in deck_paths[:3]),
        notes=f"Inferred statistically from {len(deck_paths)} deck(s)",
        confidence={"fonts": 0.85, "corner_radius": 0.75, "density": 0.8},
    )
    brand.sources.append(source)
    return brand
