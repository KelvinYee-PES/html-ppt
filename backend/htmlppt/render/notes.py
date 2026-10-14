"""PowerPoint speaker notes rendering."""
from __future__ import annotations

from pptx.slide import Slide


def render_notes(slide: Slide, notes: str) -> None:
    """Attach speaker notes text to the slide."""
    if not notes:
        return
    try:
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes
    except Exception:
        pass
