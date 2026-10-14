"""PPTX writer: renders a DeckModel into a native PowerPoint (.pptx) file."""
from __future__ import annotations

import io
from pathlib import Path

from pptx.dml.color import RGBColor

from htmlppt.brand.model import hex_to_rgb
from htmlppt.layout import model as lm
from htmlppt.render.charts import render_chart_element
from htmlppt.render.images import render_image_element
from htmlppt.render.notes import render_notes
from htmlppt.render.shapes import render_shape_element
from htmlppt.render.tables import render_table_element
from htmlppt.render.template_base import create_presentation, select_slide_layout
from htmlppt.render.text import render_text_element


def write_pptx(
    deck_model: lm.DeckModel,
    output_path: str | Path | None = None,
    template_path: str | Path | None = None,
) -> bytes:
    """Render a DeckModel into a PowerPoint presentation."""
    prs = create_presentation(deck_model.width, deck_model.height, template_path=template_path)

    for slide_model in deck_model.slides:
        layout = select_slide_layout(prs, slide_model.template_layout or slide_model.archetype)
        slide = prs.slides.add_slide(layout)

        # Clear default placeholder text if blank layout was used or if placeholders are unwanted
        for ph in list(slide.placeholders):
            try:
                # Remove shape if it's an unpopulated placeholder
                sp = ph._element
                sp.getparent().remove(sp)
            except Exception:
                pass

        # Slide background fill
        if slide_model.background:
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor(*hex_to_rgb(slide_model.background))

        # Render elements
        for el in slide_model.elements:
            if isinstance(el, lm.TextEl):
                render_text_element(slide, el)
            elif isinstance(el, lm.ShapeEl):
                render_shape_element(slide, el)
            elif isinstance(el, lm.TableEl):
                render_table_element(slide, el)
            elif isinstance(el, lm.ChartEl):
                render_chart_element(slide, el)
            elif isinstance(el, lm.ImageEl):
                render_image_element(slide, el)

        # Attach speaker notes
        if slide_model.notes:
            render_notes(slide, slide_model.notes)

    # Save to file or stream
    stream = io.BytesIO()
    prs.save(stream)
    raw_data = stream.getvalue()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_bytes(raw_data)

    return raw_data
