"""Overflow detection and slide auto-splitting."""
from __future__ import annotations

import copy
from htmlppt.analyze import ir
from htmlppt.brand.model import BrandProfile


def handle_overflow(slide: ir.Slide, brand: BrandProfile) -> list[ir.Slide]:
    """Check if slide content exceeds capacity; split into continuation slides if needed.

    The first part keeps the original slide id; continuation parts get fresh ids so
    they can be addressed individually (reorder / delete / layout override).
    """
    parts = _split(slide, brand)
    for part in parts[1:]:
        part.id = ir._id()
    return parts


def _split(slide: ir.Slide, brand: BrandProfile) -> list[ir.Slide]:
    max_bullets = brand.design.max_bullets or 6

    # 1. Check if single bullet list exceeds max_bullets
    for i, block in enumerate(slide.blocks):
        if isinstance(block, ir.BulletList) and len(block.items) > max_bullets and len(slide.blocks) == 1:
            # Split into chunks of max_bullets
            chunks = [block.items[k:k + max_bullets] for k in range(0, len(block.items), max_bullets)]
            slides_out: list[ir.Slide] = []
            for idx, chunk in enumerate(chunks):
                new_slide = copy.deepcopy(slide)
                new_slide.title = f"{slide.title} (cont.)" if idx > 0 else slide.title
                new_slide.continued = idx > 0
                new_slide.blocks = [ir.BulletList(items=chunk, ordered=block.ordered, src=block.src)]
                slides_out.append(new_slide)
            return slides_out

    # 2. Check if multiple heavyweight blocks exist on the same slide (e.g. table + chart, or 2 large tables)
    heavyweight_count = sum(1 for b in slide.blocks if isinstance(b, (ir.Table, ir.Chart, ir.CardGrid)))
    if heavyweight_count > 1 and len(slide.blocks) > 1:
        # Split heavy blocks across slides if not arranged in columns
        has_columns = any(b.column is not None for b in slide.blocks)
        if not has_columns:
            slides_out: list[ir.Slide] = []
            cur_blocks: list[ir.Block] = []
            cur_has_heavy = False
            
            for b in slide.blocks:
                is_heavy = isinstance(b, (ir.Table, ir.Chart, ir.CardGrid))
                if is_heavy and cur_has_heavy:
                    # Flush current
                    new_slide = copy.deepcopy(slide)
                    new_slide.title = f"{slide.title} (cont.)" if slides_out else slide.title
                    new_slide.continued = bool(slides_out)
                    new_slide.blocks = cur_blocks
                    slides_out.append(new_slide)
                    cur_blocks = [b]
                    cur_has_heavy = True
                else:
                    cur_blocks.append(b)
                    if is_heavy:
                        cur_has_heavy = True
            if cur_blocks:
                new_slide = copy.deepcopy(slide)
                new_slide.title = f"{slide.title} (cont.)" if slides_out else slide.title
                new_slide.continued = bool(slides_out)
                new_slide.blocks = cur_blocks
                slides_out.append(new_slide)
            return slides_out

    return [slide]
