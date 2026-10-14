"""Native PowerPoint editable chart rendering."""
from __future__ import annotations

from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.slide import Slide
from pptx.util import Emu, Pt

from htmlppt.brand.model import hex_to_rgb
from htmlppt.layout import model as lm


def _get_chart_type(spec) -> XL_CHART_TYPE:
    t = spec.type.lower()
    horiz = spec.horizontal
    stacked = spec.stacked

    if t in ("bar", "column"):
        if horiz:
            return XL_CHART_TYPE.BAR_STACKED if stacked else XL_CHART_TYPE.BAR_CLUSTERED
        else:
            return XL_CHART_TYPE.COLUMN_STACKED if stacked else XL_CHART_TYPE.COLUMN_CLUSTERED
    elif t == "line":
        return XL_CHART_TYPE.LINE
    elif t == "area":
        return XL_CHART_TYPE.AREA
    elif t == "pie":
        return XL_CHART_TYPE.PIE
    elif t == "doughnut":
        return XL_CHART_TYPE.DOUGHNUT
    elif t == "radar":
        return XL_CHART_TYPE.RADAR

    return XL_CHART_TYPE.COLUMN_CLUSTERED


def render_chart_element(slide: Slide, el: lm.ChartEl) -> None:
    """Render a native editable PowerPoint chart with an embedded data sheet."""
    spec = el.spec
    chart_type = _get_chart_type(spec)

    chart_data = CategoryChartData()
    # Populate categories
    chart_data.categories = spec.categories or ["Item 1"]

    # Populate series
    for s in spec.series:
        # None values converted to 0
        vals = [0.0 if v is None else float(v) for v in (s.values or [])]
        # Pad values if fewer than categories
        if len(vals) < len(chart_data.categories):
            vals += [0.0] * (len(chart_data.categories) - len(vals))
        chart_data.add_series(s.name or "Series", tuple(vals))

    graphic_frame = slide.shapes.add_chart(
        chart_type, Emu(el.x), Emu(el.y), Emu(el.w), Emu(el.h), chart_data
    )
    chart = graphic_frame.chart

    # Legend configuration
    chart.has_legend = el.legend
    if el.legend and chart.legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False
        chart.legend.font.name = el.font
        chart.legend.font.size = Pt(el.font_size)
        if el.text_color:
            chart.legend.font.color.rgb = RGBColor(*hex_to_rgb(el.text_color))

    # Apply brand series palette colors
    palette = el.palette or ["2563EB", "0EA5E9", "10B981", "F59E0B", "EF4444"]
    for i, series in enumerate(chart.series):
        hex_color = palette[i % len(palette)]
        try:
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = RGBColor(*hex_to_rgb(hex_color))
        except Exception:
            pass
        # If line chart, also color the line
        if spec.type == "line":
            try:
                series.format.line.color.rgb = RGBColor(*hex_to_rgb(hex_color))
                series.format.line.width = Pt(2.0)
            except Exception:
                pass

    # Category and value axes font styling
    try:
        if chart.category_axis:
            chart.category_axis.tick_labels.font.name = el.font
            chart.category_axis.tick_labels.font.size = Pt(el.font_size)
            if el.text_color:
                chart.category_axis.tick_labels.font.color.rgb = RGBColor(*hex_to_rgb(el.text_color))
    except Exception:
        pass

    try:
        if chart.value_axis:
            chart.value_axis.tick_labels.font.name = el.font
            chart.value_axis.tick_labels.font.size = Pt(el.font_size)
            if el.text_color:
                chart.value_axis.tick_labels.font.color.rgb = RGBColor(*hex_to_rgb(el.text_color))
    except Exception:
        pass
