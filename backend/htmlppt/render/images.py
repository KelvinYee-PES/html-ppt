"""Native PowerPoint picture rendering."""
from __future__ import annotations

import base64
import io
from pptx.slide import Slide
from pptx.util import Emu

from htmlppt.layout import model as lm


def render_image_element(slide: Slide, el: lm.ImageEl) -> None:
    """Render a picture shape from base64 image data."""
    if not el.b64:
        return
    try:
        raw_bytes = base64.b64decode(el.b64)
        stream = io.BytesIO(raw_bytes)
        slide.shapes.add_picture(stream, Emu(el.x), Emu(el.y), Emu(el.w), Emu(el.h))
    except Exception:
        pass
