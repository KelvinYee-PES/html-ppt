"""Turn a DOM snapshot into a semantic Deck.

Deck mode: the HTML already contains slides (reveal.js, `.slide`, `<section>`
at ~16:9). Page mode: a long report/dashboard is split at headings.
"""
from __future__ import annotations

import re

from htmlppt.analyze import ir
from htmlppt.analyze.classifier import (CLOSING_RE, Ctx, _all, classify, compute_body_fs, text_of)


def build_deck(snap: dict) -> ir.Deck:
    root = snap.get("root")
    if not root:
        return ir.Deck(warnings=["empty document"])
    ctx = Ctx(body_fs=compute_body_fs(root), charts=snap.get("charts", []))
    slide_nodes = find_slide_nodes(root)
    if slide_nodes:
        deck = _deck_mode(slide_nodes, ctx)
    else:
        deck = _page_mode(root, ctx, snap)
    if not deck.meta.title:
        deck.meta.title = snap.get("title") or (deck.slides[0].title if deck.slides else "")
    deck.warnings.extend(ctx.warnings)
    return deck


# ---------------------------------------------------------------- slide discovery

def find_slide_nodes(root: dict) -> list[dict]:
    marked = [n for n in _all(root) if (n.get("data") or {}).get("hpSlide") == "1"]
    if len(marked) >= 2:
        return marked
    # containers whose children are mostly ~16:9 boxes of the same size
    best: list[dict] = []
    for n in _all(root):
        kids = [k for k in n.get("kids", []) or [] if k["box"]["w"] >= 600]
        if len(kids) < 2:
            continue
        ratios = [k["box"]["w"] / max(k["box"]["h"], 1) for k in kids]
        good = [k for k, r in zip(kids, ratios) if 1.25 <= r <= 2.1]
        if len(good) >= 2 and len(good) >= 0.8 * len(kids):
            w0 = good[0]["box"]["w"]
            if all(abs(k["box"]["w"] - w0) < 0.1 * w0 for k in good) and len(good) > len(best):
                best = good
    return best


# ---------------------------------------------------------------- deck mode

def _deck_mode(nodes: list[dict], ctx: Ctx) -> ir.Deck:
    deck = ir.Deck(source_kind="deck")
    for i, n in enumerate(nodes):
        ctx.slide_box = n["box"]
        blocks = classify(n, ctx)
        slide = ir.Slide(source_index=i)
        _extract_title(slide, blocks)
        slide.blocks = blocks
        _infer_kind(slide, i, len(nodes))
        deck.slides.append(slide)
    if deck.slides and deck.slides[0].kind == "title":
        deck.meta.title = deck.slides[0].title
        deck.meta.subtitle = deck.slides[0].subtitle
    return deck


def _extract_title(slide: ir.Slide, blocks: list) -> None:
    heads = [(i, b) for i, b in enumerate(blocks) if isinstance(b, ir.Heading)]
    if not heads:
        return
    # prefer the topmost heading on the page (design decks put the page title in a
    # flex header that may be column-tagged); fall back to declaration order
    def rank(ib):
        i, b = ib
        y = b.src["y"] if b.src else float(i) * 1e6
        return (y, b.level, i)
    i, h = min(heads, key=rank)
    slide.title = ir.runs_text(h.runs).strip()
    blocks.pop(i)
    # kicker before title (short caption) or subtitle right after
    if i < len(blocks):
        nxt = blocks[i]
        if isinstance(nxt, ir.Paragraph) and len(ir.runs_text(nxt.runs)) < 180 and nxt.column is None \
                and (nxt.role in ("lead", "caption") or _close_below(h, nxt)):
            slide.subtitle = ir.runs_text(nxt.runs).strip()
            blocks.pop(i)
    if i > 0 and not slide.subtitle:
        prev = blocks[i - 1]
        if isinstance(prev, ir.Paragraph) and prev.role == "caption" and len(ir.runs_text(prev.runs)) < 50:
            slide.subtitle = ir.runs_text(prev.runs).strip()
            blocks.pop(i - 1)


def _close_below(a, b) -> bool:
    if not a.src or not b.src:
        return False
    return 0 <= b.src["y"] - (a.src["y"] + a.src["h"]) < 40 and len(ir.runs_text(b.runs)) < 140


def _infer_kind(slide: ir.Slide, idx: int, total: int) -> None:
    simple = all(isinstance(b, (ir.Paragraph, ir.Heading)) for b in slide.blocks)
    small = sum(len(ir.runs_text(b.runs)) for b in slide.blocks if hasattr(b, "runs")) < 200
    if idx == 0 and slide.title and simple and len(slide.blocks) <= 2 and small:
        slide.kind = "title"
        if not slide.subtitle and slide.blocks:
            slide.subtitle = ir.runs_text(slide.blocks[0].runs).strip()
            slide.blocks = slide.blocks[1:]
    elif idx == total - 1 and CLOSING_RE.search(slide.title or "") and simple:
        slide.kind = "closing"
    elif slide.title and not slide.blocks:
        slide.kind = "section"
    elif slide.title and simple and len(slide.blocks) == 1 and small and re.match(r"^(\d+|[IVX]+)[.)]?\s", slide.title):
        slide.kind = "section"


# ---------------------------------------------------------------- page mode

def _page_mode(root: dict, ctx: Ctx, snap: dict) -> ir.Deck:
    deck = ir.Deck(source_kind="page")
    main = next((n for n in _all(root) if n["tag"] in ("main", "article")), root)
    ctx.slide_box = main["box"]
    blocks = classify(main, ctx)
    if main is not root:  # header outside <main> may carry the report title
        header = next((n for n in _all(root) if n["tag"] == "header"), None)
        if header:
            ctx.slide_box = header["box"]
            blocks = classify(header, ctx) + blocks

    levels = [b.level for b in blocks if isinstance(b, ir.Heading) and b.column is None]
    if not levels:
        deck.slides.append(ir.Slide(title=snap.get("title", ""), blocks=blocks, source_index=0))
        return deck
    top = min(levels)
    title_head = None
    if levels.count(top) == 1 and any(l > top for l in levels):
        title_head = top
        split = min(l for l in levels if l > top)
    else:
        split = top

    current: ir.Slide | None = None
    pre: list = []
    seg = 0
    for b in blocks:
        if isinstance(b, ir.Heading) and b.column is None and b.level == title_head:
            deck.meta.title = ir.runs_text(b.runs).strip()
            continue
        if isinstance(b, ir.Heading) and b.column is None and b.level <= split:
            current = ir.Slide(title=ir.runs_text(b.runs).strip(), source_index=seg)
            seg += 1
            deck.slides.append(current)
            continue
        if current is None:
            pre.append(b)
        else:
            current.blocks.append(b)

    # content before the first section heading: subtitle + intro
    if pre:
        first = pre[0]
        if isinstance(first, ir.Paragraph) and len(ir.runs_text(first.runs)) < 180:
            deck.meta.subtitle = ir.runs_text(first.runs).strip()
            pre = pre[1:]
        if pre:
            deck.slides.insert(0, ir.Slide(title="Overview" if deck.meta.title else snap.get("title", ""),
                                           blocks=pre, source_index=-1))
    for s in deck.slides:
        _subtitle_from_lead(s)
    # a section with only a lone sub-heading list -> keep sub-headings as blocks (handled by layout)
    deck.slides = [s for s in deck.slides if s.blocks or s.title]
    return deck


def _subtitle_from_lead(slide: ir.Slide) -> None:
    if slide.blocks and isinstance(slide.blocks[0], ir.Paragraph) and slide.blocks[0].role == "lead" \
            and len(ir.runs_text(slide.blocks[0].runs)) < 160:
        slide.subtitle = ir.runs_text(slide.blocks[0].runs).strip()
        slide.blocks = slide.blocks[1:]


def describe(deck: ir.Deck) -> str:
    """Human-readable summary (debugging / CLI --explain)."""
    lines = [f"Deck: {deck.meta.title!r} ({deck.source_kind}, {len(deck.slides)} slides)"]
    for i, s in enumerate(deck.slides, 1):
        lines.append(f"{i:>2}. [{s.kind}] {s.title!r}" + (f" — {s.subtitle!r}" if s.subtitle else ""))
        for b in s.blocks:
            extra = ""
            if isinstance(b, ir.BulletList):
                extra = f"{len(b.items)} items"
            elif isinstance(b, ir.Table):
                extra = f"{len(b.rows)}x{len(b.rows[0]) if b.rows else 0}"
            elif isinstance(b, ir.Chart):
                extra = f"{b.spec.type} {len(b.spec.series)} series"
            elif isinstance(b, ir.KPIGroup):
                extra = ", ".join(k.value for k in b.items)
            elif isinstance(b, ir.CardGrid):
                extra = f"{b.variant} x{len(b.cards)}"
            elif hasattr(b, "runs"):
                extra = repr(ir.runs_text(b.runs)[:50])
            col = f" col{b.column}" if b.column is not None else ""
            lines.append(f"      - {b.type}{col}: {extra}")
    return "\n".join(lines)
