"""Rule-based classification of DOM snapshot nodes into semantic IR blocks.

Recognises headings, paragraphs, bullet lists, tables, charts, KPI tiles, card
grids / process steps / timelines, callouts, quotes, images and SVG graphics.
Positioned/overlapping compositions that can't be understood semantically are
kept as a `Freeform` block (coordinate-faithful fallback).
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from htmlppt.analyze import ir

NUM_RE = re.compile(r"^[\s€$£¥+\-−~≈<>]*\d[\d.,\s]*\s*(%|[kKmMbBtT]|bn|mn|Mio\.?|Mrd\.?|pp|x|×|€|\$|£|/\w+)?\s*\+?$")
DELTA_RE = re.compile(r"([▲▼↑↓△▽⬆⬇]|^[+\-−]\s?\d|\bvs\.?\b|\bYoY\b|\bQoQ\b|pp\b)", re.I)
DATE_RE = re.compile(r"\b(Q[1-4]|H[12]|FY|20\d\d|19\d\d|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Phase|Week|Month)\b", re.I)
STEP_RE = re.compile(r"^(step|phase|stage|stufe|schritt)?\s*0?\d{1,2}[.:)]?$|^(step|phase|stage)\b", re.I)
CLOSING_RE = re.compile(r"\b(thank you|thanks|questions\??|q\s?&\s?a|contact us|danke|merci)\b", re.I)


@dataclass
class Ctx:
    body_fs: float = 16.0
    charts: list[dict] = field(default_factory=list)
    slide_box: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- helpers

def text_of(n: dict) -> str:
    if n.get("runs"):
        return "".join(r.get("t", "") for r in n["runs"])
    if n["tag"] == "list":
        return " ".join("".join(r.get("t", "") for r in it["runs"]) for it in n["items"])
    return " ".join(text_of(k) for k in n.get("kids", []) or [])


def leaves(n: dict) -> list[dict]:
    """All descendant nodes that are terminal (text leaves, lists, tables, media)."""
    if n.get("runs") is not None or n["tag"] in ("list", "table", "chart", "img", "canvas", "svg", "hr"):
        return [n]
    out = []
    for k in n.get("kids", []) or []:
        out.extend(leaves(k))
    return out


def text_leaves(n: dict) -> list[dict]:
    return [l for l in leaves(n) if l.get("runs")]


def has_visual(n: dict) -> bool:
    v = n.get("v") or {}
    return bool(v.get("bg") or v.get("grad") or v.get("border") or v.get("borders") or v.get("shadow"))


def compute_body_fs(root: dict) -> float:
    weights: dict[float, int] = {}
    for l in text_leaves(root):
        t = text_of(l)
        if len(t) > 30:
            weights[l.get("fs", 16)] = weights.get(l.get("fs", 16), 0) + len(t)
    for n in _all(root):
        if n["tag"] == "list":
            weights[n.get("fs", 16)] = weights.get(n.get("fs", 16), 0) + len(text_of(n))
    if not weights:
        return 16.0
    return max(weights.items(), key=lambda kv: kv[1])[0]


def _all(n: dict):
    yield n
    for k in n.get("kids", []) or []:
        yield from _all(k)


def to_runs(raw: list[dict], base_color: str | None = None) -> list[ir.Run]:
    out: list[ir.Run] = []
    colors = [r.get("c") for r in raw if r.get("t", "").strip()]
    dominant = base_color or (statistics.mode(colors) if colors else None)
    for r in raw:
        t = r.get("t", "")
        if r.get("up"):
            t = t.upper()
        out.append(ir.Run(
            t=t, b=bool(r.get("b")), i=bool(r.get("i")), u=bool(r.get("u")) and not r.get("href"),
            strike=bool(r.get("st")), color=r.get("c"), href=r.get("href"), mono=bool(r.get("mono")),
            sup=bool(r.get("sup")), sub=bool(r.get("sub")),
            emphasis=bool(r.get("hl")) or (r.get("c") is not None and dominant is not None and r.get("c") != dominant),
        ))
    return out


def rel_box(n: dict, ctx: Ctx) -> dict:
    sb = ctx.slide_box or {"x": 0, "y": 0, "w": 1920, "h": 1080}
    b = n["box"]
    return {"x": b["x"] - sb["x"], "y": b["y"] - sb["y"], "w": b["w"], "h": b["h"], "sw": sb["w"], "sh": sb["h"]}


def _align(ta: str | None) -> str:
    return ta if ta in ("center", "right") else "left"


def _sentiment(text: str, color: str | None) -> str:
    if color:
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        if g > r + 30 and g > b:
            return "positive"
        if r > g + 40 and r > b + 20:
            return "negative"
    if re.search(r"[▲↑⬆]|^\+", text):
        return "positive"
    if re.search(r"[▼↓⬇]|^[\-−]", text):
        return "negative"
    return "neutral"


# ---------------------------------------------------------------- leaf classification

def heading_level(n: dict, ctx: Ctx) -> int | None:
    tag = n["tag"]
    if re.fullmatch(r"h[1-6]", tag):
        return int(tag[1])
    t = text_of(n).strip()
    if not t or len(t) > 120 or "\n" in t:
        return None
    fs = n.get("fs", ctx.body_fs)
    bold = (n.get("fw") or 400) >= 600 or all(r.get("b") for r in n.get("runs", []) if r.get("t", "").strip())
    ratio = fs / max(ctx.body_fs, 1)
    if NUM_RE.match(t):
        return None
    if ratio >= 2.2:
        return 1
    if ratio >= 1.5:
        return 2
    if ratio >= 1.15 and bold:
        return 3
    if bold and ratio >= 1.0 and len(t) < 60 and not t.endswith((".", ":")) and len(n.get("runs", [])) <= 2:
        return 4
    return None


def classify_leaf(n: dict, ctx: Ctx) -> list[ir.Block]:
    tag = n["tag"]
    src = rel_box(n, ctx)
    if tag == "list":
        items = [ir.ListItem(runs=to_runs(it["runs"]), level=min(it["level"], 4)) for it in n["items"] if it["runs"]]
        return [ir.BulletList(items=items, ordered=n.get("ordered", False), src=src)] if items else []
    if tag == "table":
        return [build_table(n, src)]
    if tag == "chart":
        c = next((c for c in ctx.charts if c["index"] == n.get("chart")), None)
        if c:
            try:
                return [ir.Chart(spec=normalize_chart(c["spec"]), src=src)]
            except Exception as e:  # pragma: no cover - defensive
                ctx.warnings.append(f"chart parse failed: {e}")
        return []
    if tag in ("img", "canvas"):
        img = n.get("img")
        if not img:
            return []
        b = n["box"]
        return [ir.Image(mime=img["mime"], b64=img["b64"], w=n.get("nw") or b["w"], h=n.get("nh") or b["h"],
                         alt=n.get("alt", ""), src=src,
                         is_logo="logo" in (n.get("alt", "") + n.get("cls", "")).lower())]
    if tag == "svg":
        b = n["box"]
        return [ir.VectorGraphic(svg=n["svg"], w=b["w"], h=b["h"], icon=max(b["w"], b["h"]) <= 72, src=src)]
    if tag == "hr":
        return []
    if not n.get("runs"):
        return []
    runs = to_runs(n["runs"])
    text = ir.runs_text(runs).strip()
    if not text:
        return []
    if tag in ("blockquote", "q"):
        return [ir.Quote(runs=runs, src=src)]
    lvl = heading_level(n, ctx)
    if lvl is not None:
        return [ir.Heading(level=lvl, runs=_strip_styles(runs), src=src)]
    fs = n.get("fs", ctx.body_fs)
    role = "body"
    if fs >= ctx.body_fs * 1.15 and len(text) < 220:
        role = "lead"
    elif fs <= ctx.body_fs * 0.8:
        role = "caption" if len(text) < 160 else "footnote"
    if has_visual(n) and len(text) < 300 and (n.get("v") or {}).get("bg"):
        return [ir.Callout(runs=runs, tone=_tone(n), src=src)]
    return [ir.Paragraph(runs=runs, role=role, align=_align(n.get("ta")), src=src)]


def _strip_styles(runs: list[ir.Run]) -> list[ir.Run]:
    return [r.model_copy(update={"b": False, "color": None, "emphasis": r.emphasis}) for r in runs]


def _tone(n: dict) -> str:
    v = n.get("v") or {}
    s = _sentiment("", v.get("bg") or (v.get("border") or {}).get("c"))
    if s == "positive":
        return "positive"
    if s == "negative":
        return "negative"
    return "info"


def build_table(n: dict, src: dict) -> ir.Table:
    rows: list[list[ir.Cell]] = []
    header_rows = 0
    for ri, row in enumerate(n["rows"]):
        cells = []
        for c in row["cells"]:
            runs = to_runs(c["runs"])
            txt = ir.runs_text(runs).strip()
            numeric = bool(NUM_RE.match(txt)) or bool(re.match(r"^[+\-−]?\d", txt))
            align = c.get("ta") if c.get("ta") in ("center", "right") else ("right" if numeric and ri > 0 else "left")
            tone = "none"
            if numeric and txt[:1] in "+-−":
                s = _sentiment(txt, c.get("c"))
                tone = s if s in ("positive", "negative") else "none"
            cells.append(ir.Cell(runs=runs, colspan=c.get("cs", 1), rowspan=c.get("rs", 1), header=bool(c.get("th")) and ri == header_rows,
                                 align=align, bold=bool(c.get("b")), tone=tone))
        if (row.get("head") or (cells and all(x.header for x in cells))) and ri == header_rows:
            header_rows += 1
        rows.append(cells)
    widths = [c.get("w", 1) for c in n["rows"][0]["cells"]] if n["rows"] else []
    last = rows[-1] if rows else []
    total = bool(last) and (ir.runs_text(last[0].runs).strip().lower().startswith(("total", "sum", "gesamt"))
                            or all(c.bold or all(r.b for r in c.runs) for c in last))
    return ir.Table(rows=rows, header_rows=header_rows, caption=n.get("caption", ""), col_weights=widths,
                    total_row=total and len(rows) > 2, src=src)


def normalize_chart(spec: dict) -> ir.ChartSpec:
    typ = spec.get("type") or "bar"
    if typ not in ("bar", "line", "area", "pie", "doughnut", "scatter", "radar"):
        typ = "bar"
    series = []
    for s in spec.get("series", []):
        vals = [None if v is None else float(v) for v in (s.get("values") or [])]
        xy = s.get("xy")
        series.append(ir.Series(name=s.get("name") or "", values=vals, xy=xy, type=s.get("type")))
    cats = [str(c) for c in spec.get("categories", [])]
    if typ not in ("scatter",) and series and not cats:
        cats = [str(i + 1) for i in range(max(len(s.values) for s in series))]
    return ir.ChartSpec(type=typ, horizontal=bool(spec.get("horizontal")), stacked=bool(spec.get("stacked")),
                        title=spec.get("title") or "", categories=cats, series=series,
                        x_title=spec.get("x_title") or "", y_title=spec.get("y_title") or "",
                        show_legend=bool(spec.get("show_legend", True)) and (len(series) > 1 or typ in ("pie", "doughnut")))


# ---------------------------------------------------------------- composite detection

def _kpi_from(n: dict, ctx: Ctx) -> ir.KPI | None:
    tl = text_leaves(n)
    if not 1 <= len(tl) <= 5:
        return None
    if any(l["tag"] in ("list", "table", "chart") for l in leaves(n)):
        return None
    cands = [l for l in tl if NUM_RE.match(text_of(l).strip()) and len(text_of(l).strip()) <= 16]
    if not cands:
        return None
    val = max(cands, key=lambda l: l.get("fs", 0))
    others = [l for l in tl if l is not val]
    if others and val.get("fs", 0) < 1.35 * max(o.get("fs", 0) for o in others):
        return None
    if not others and val.get("fs", 0) < ctx.body_fs * 1.6:
        return None
    delta = next((o for o in others if DELTA_RE.search(text_of(o))), None)
    labels = [o for o in others if o is not delta]
    label = " ".join(text_of(o).strip() for o in labels)
    dt = text_of(delta).strip() if delta else ""
    trend = "none"
    if dt:
        trend = "up" if re.search(r"[▲↑⬆]|^\+", dt) else "down" if re.search(r"[▼↓⬇]|^[\-−]", dt) else "flat"
    return ir.KPI(value=text_of(val).strip(), label=label[:120], delta=dt,
                  trend=trend, sentiment=_sentiment(dt, delta.get("c") if delta else None) if dt else "neutral")


def _similar_sizes(kids: list[dict], tol: float = 0.3) -> bool:
    ws = [k["box"]["w"] for k in kids]
    hs = [k["box"]["h"] for k in kids]
    return (max(ws) - min(ws)) <= tol * max(ws) and (max(hs) - min(hs)) <= max(tol * max(hs), 40)


def _horizontal(kids: list[dict]) -> bool:
    """True if the kids are laid out side-by-side (at least one row with 2+ items)."""
    if len(kids) < 2:
        return False
    a, b = kids[0]["box"], kids[1]["box"]
    ov = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
    return ov > 0.4 * min(a["h"], b["h"]) and b["x"] >= a["x"] + a["w"] - 4


def try_kpis(kids: list[dict], ctx: Ctx, src: dict) -> ir.KPIGroup | None:
    if len(kids) < 2 or len(kids) > 8:
        return None
    kpis = [_kpi_from(k, ctx) for k in kids]
    if sum(k is not None for k in kpis) < max(2, int(0.75 * len(kids))):
        return None
    return ir.KPIGroup(items=[k for k in kpis if k], src=src)


def _card_from(n: dict, ctx: Ctx) -> ir.Card | None:
    ls = leaves(n)
    if any(l["tag"] in ("table", "chart") for l in ls):
        return None
    tl = [l for l in ls if l.get("runs")]
    if not tl and not any(l["tag"] == "list" for l in ls):
        return None
    card = ir.Card()
    icon = next((l for l in ls if l["tag"] == "svg" and max(l["box"]["w"], l["box"]["h"]) <= 80), None)
    if icon:
        card.icon_svg = icon["svg"]
    # title = heading-like leaf with the largest font (ties: first)
    scored = sorted(tl, key=lambda l: (-(l.get("fs", 0) + (4 if (l.get("fw") or 400) >= 600 else 0)), tl.index(l)))
    title = scored[0] if scored else None
    if title is not None and len(text_of(title)) > 90:
        title = None
    for l in ls:
        if l is title:
            card.title = text_of(l).strip()
        elif l["tag"] == "list":
            card.bullets.extend(ir.ListItem(runs=to_runs(it["runs"]), level=it["level"]) for it in l["items"])
        elif l.get("runs"):
            t = text_of(l).strip()
            before_title = title is not None and l["box"]["y"] < title["box"]["y"] - 2
            if not card.kicker and (before_title or (title is None and not card.title)) and len(t) <= 40:
                card.kicker = t
            else:
                if card.body:
                    card.body.append(ir.Run(t="\n"))
                card.body.extend(to_runs(l["runs"]))
    if not (card.title or card.body or card.bullets):
        return None
    return card


def try_cards(parent: dict, kids: list[dict], ctx: Ctx, src: dict) -> ir.CardGrid | None:
    if len(kids) < 2 or len(kids) > 12:
        return None
    if not _horizontal(kids) and not (parent.get("gridCols", 0) >= 2):
        return None
    visual = sum(has_visual(k) for k in kids)
    if visual < 0.6 * len(kids) and len(kids) < 3:
        return None
    if not _similar_sizes(kids, 0.35):
        return None
    cards = [_card_from(k, ctx) for k in kids]
    if any(c is None for c in cards):
        return None
    kickers = [c.kicker for c in cards if c.kicker]
    variant = "cards"
    if len(kickers) >= 0.75 * len(cards):
        if all(STEP_RE.match(k) for k in kickers):
            variant = "process"
        elif all(DATE_RE.search(k) for k in kickers):
            variant = "timeline"
    return ir.CardGrid(cards=cards, variant=variant, src=src)


def _is_decorative(n: dict) -> bool:
    return n.get("pos") in ("absolute", "fixed") and not text_of(n).strip() and \
        not any(l["tag"] in ("img", "chart", "canvas", "table") for l in leaves(n))


def _overlapping(kids: list[dict]) -> bool:
    boxes = [k["box"] for k in kids if k["box"]["w"] > 4 and k["box"]["h"] > 4]
    hits = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
            oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
            if ox > 8 and oy > 8 and ox * oy > 0.15 * min(a["w"] * a["h"], b["w"] * b["h"]):
                hits += 1
    return hits >= 2


def build_freeform(n: dict, ctx: Ctx) -> ir.Freeform:
    sb = dict(n["box"])
    sb["w"], sb["h"] = max(sb["w"], 1), max(sb["h"], 1)
    els: list[ir.FreeElement] = []

    def add(node: dict):
        b = node["box"]
        rx, ry = (b["x"] - sb["x"]) / sb["w"], (b["y"] - sb["y"]) / sb["h"]
        rw, rh = b["w"] / sb["w"], b["h"] / sb["h"]
        v = node.get("v") or {}
        if has_visual(node) and node is not n:
            border = v.get("border") or {}
            els.append(ir.FreeElement(kind="box", x=rx, y=ry, w=rw, h=rh, fill=v.get("bg") or (v.get("grad") or [None])[0],
                                      fill_alpha=v.get("bgA", 1.0), border=border.get("c"), border_w=border.get("w", 0),
                                      radius_px=v.get("radius", 0)))
        if node.get("runs"):
            tb = node.get("tbox") or b
            els.append(ir.FreeElement(kind="text", x=(tb["x"] - sb["x"]) / sb["w"], y=(tb["y"] - sb["y"]) / sb["h"],
                                      w=max(tb["w"], 10) / sb["w"], h=max(tb["h"], 10) / sb["h"],
                                      runs=to_runs(node["runs"]), font_px=node.get("fs", 16), align=_align(node.get("ta")),
                                      bold=(node.get("fw") or 400) >= 600, color=node.get("c")))
            return
        if node["tag"] in ("img", "canvas") and node.get("img"):
            els.append(ir.FreeElement(kind="image", x=rx, y=ry, w=rw, h=rh, b64=node["img"]["b64"], mime=node["img"]["mime"]))
            return
        if node["tag"] == "svg":
            els.append(ir.FreeElement(kind="vector", x=rx, y=ry, w=rw, h=rh, svg=node["svg"]))
            return
        if node["tag"] == "hr":
            els.append(ir.FreeElement(kind="line", x=rx, y=ry, w=rw, h=0, border=node.get("c")))
            return
        if node["tag"] == "list":
            for it in node["items"]:
                ib = it["box"]
                els.append(ir.FreeElement(kind="text", x=(ib["x"] - sb["x"]) / sb["w"], y=(ib["y"] - sb["y"]) / sb["h"],
                                          w=ib["w"] / sb["w"], h=ib["h"] / sb["h"],
                                          runs=[ir.Run(t="• ")] + to_runs(it["runs"]), font_px=node.get("fs", 16)))
            return
        for k in node.get("kids", []) or []:
            add(k)

    add(n)
    return ir.Freeform(elements=els, aspect=sb["w"] / max(sb["h"], 1), src=rel_box(n, ctx))


# ---------------------------------------------------------------- main recursion

def classify(n: dict, ctx: Ctx, column: int | None = None) -> list[ir.Block]:
    if n.get("runs") is not None or n["tag"] in ("list", "table", "chart", "img", "canvas", "svg", "hr", "#text"):
        blocks = classify_leaf(n, ctx)
        for b in blocks:
            b.column = column
        return blocks

    kids = [k for k in (n.get("kids") or []) if not _is_decorative(k)]
    if not kids:
        return []
    src = rel_box(n, ctx)

    def tag(blocks: list[ir.Block]) -> list[ir.Block]:
        for b in blocks:
            if b.column is None:
                b.column = column
        return blocks

    # Freeform: absolutely positioned / overlapping compositions (diagrams, infographics)
    absolute = sum(1 for k in kids if k.get("pos") == "absolute")
    if (absolute >= 3 or _overlapping(kids)) and text_of(n).strip():
        return tag([build_freeform(n, ctx)])

    # Callout: a visually boxed container holding only short text
    tl = text_leaves(n)
    ls = leaves(n)
    if has_visual(n) and (n.get("v") or {}).get("bg") and 1 <= len(tl) <= 3 and len(ls) == len(tl) \
            and n["box"]["w"] < 0.95 * ctx.slide_box.get("w", 1e9) and len(text_of(n)) < 400:
        title = ""
        runs_src = tl
        if len(tl) >= 2 and ((tl[0].get("fw") or 400) >= 600 or tl[0].get("fs", 0) > tl[1].get("fs", 0)):
            title, runs_src = text_of(tl[0]).strip(), tl[1:]
        runs: list[ir.Run] = []
        for i, l in enumerate(runs_src):
            if i:
                runs.append(ir.Run(t="\n"))
            runs.extend(to_runs(l["runs"]))
        if not NUM_RE.match(text_of(n).strip()):
            return tag([ir.Callout(runs=runs, title=title, tone=_tone(n), src=src)])

    meaningful = [k for k in kids if text_of(k).strip() or leaves(k) and any(l["tag"] in ("img", "chart", "canvas", "table", "svg") for l in leaves(k))]
    if len(meaningful) >= 2:
        kpis = try_kpis(meaningful, ctx, src)
        if kpis:
            return tag([kpis])
        cards = try_cards(n, meaningful, ctx, src)
        if cards:
            return tag([cards])
        if _horizontal(meaningful) and column is None and len(meaningful) <= 3:
            out: list[ir.Block] = []
            for i, k in enumerate(meaningful):
                out.extend(classify(k, ctx, column=i))
            return out

    out = []
    for k in kids:
        out.extend(classify(k, ctx, column))
    return _merge_quote_attribution(out)


def _merge_quote_attribution(blocks: list[ir.Block]) -> list[ir.Block]:
    out: list[ir.Block] = []
    for b in blocks:
        prev = out[-1] if out else None
        if isinstance(prev, ir.Quote) and isinstance(b, ir.Paragraph):
            t = ir.runs_text(b.runs).strip()
            if t[:1] in "—–-~" and len(t) < 120:
                prev.attribution = t.lstrip("—–-~ ").strip()
                continue
        out.append(b)
    return out
