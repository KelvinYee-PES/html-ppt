"""Layout grid calculation and bounding boxes."""
from __future__ import annotations

from dataclasses import dataclass
from htmlppt.brand.model import BrandProfile


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h


@dataclass
class SlideGeometry:
    width: int
    height: int
    margin_x: int
    margin_top: int
    margin_bottom: int
    gutter: int

    # Computed zones
    title_rect: Rect
    content_rect: Rect

    @classmethod
    def from_brand(cls, brand: BrandProfile, has_title: bool = True) -> SlideGeometry:
        sw = brand.slide_size.width
        sh = brand.slide_size.height
        mx = brand.design.margin_x
        mt = brand.design.margin_top
        mb = brand.design.margin_bottom
        gutter = brand.design.gutter

        # Header zone takes ~18% of slide height if title present
        if has_title:
            title_h = int(sh * 0.16)
            title_rect = Rect(x=mx, y=mt, w=sw - 2 * mx, h=title_h)
            content_y = title_rect.bottom + int(gutter * 0.5)
            content_h = sh - content_y - mb
            content_rect = Rect(x=mx, y=content_y, w=sw - 2 * mx, h=content_h)
        else:
            title_rect = Rect(x=mx, y=mt, w=0, h=0)
            content_rect = Rect(x=mx, y=mt, w=sw - 2 * mx, h=sh - mt - mb)

        return cls(
            width=sw,
            height=sh,
            margin_x=mx,
            margin_top=mt,
            margin_bottom=mb,
            gutter=gutter,
            title_rect=title_rect,
            content_rect=content_rect,
        )

    def split_columns(self, n_cols: int) -> list[Rect]:
        """Split content area horizontally into n columns with gutter."""
        if n_cols <= 1:
            return [self.content_rect]
        total_gutter = self.gutter * (n_cols - 1)
        avail_w = self.content_rect.w - total_gutter
        col_w = avail_w // n_cols
        
        cols: list[Rect] = []
        for i in range(n_cols):
            cx = self.content_rect.x + i * (col_w + self.gutter)
            cols.append(Rect(x=cx, y=self.content_rect.y, w=col_w, h=self.content_rect.h))
        return cols

    def split_rows(self, n_rows: int) -> list[Rect]:
        """Split content area vertically into n rows with gutter."""
        if n_rows <= 1:
            return [self.content_rect]
        total_gutter = self.gutter * (n_rows - 1)
        avail_h = self.content_rect.h - total_gutter
        row_h = avail_h // n_rows
        
        rows: list[Rect] = []
        for i in range(n_rows):
            cy = self.content_rect.y + i * (row_h + self.gutter)
            rows.append(Rect(x=self.content_rect.x, y=cy, w=self.content_rect.w, h=row_h))
        return rows
