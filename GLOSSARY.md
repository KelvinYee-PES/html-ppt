# HTML-PPT Domain Glossary

Converts rich HTML presentation decks into native, brand-compliant PowerPoint (.pptx) presentations and live previews while preserving visual hierarchy, context, and aesthetic elegance.

## Language

**Archetype**:
The visual layout template assigned to a slide based on its content structure (e.g., `kpi_grid`, `cards`, `table`, `two_column`, `quote`, `title`).
_Avoid_: Template, layout style, page type

**BrandProfile**:
The complete specification of colors, typography hierarchy, margins, and design treatments applied during layout.
_Avoid_: Theme config, style settings

**DeckModel**:
The fully positioned, coordinate-resolved geometric representation of a presentation deck ready for rendering to PPTX or preview canvas.
_Avoid_: Output JSON, layout tree

**Curated Palette**:
A curated set of harmonious theme colors (accents, dark backgrounds, surfaces) used when no uploaded brand profile exists.
_Avoid_: Default colors, fallback theme

**CardGrid**:
A structured group of related content blocks displayed as distinct visual cards with consistent padding, elevation, or borders.
_Avoid_: Box group, panel list

**KPIGroup**:
A row or grid of prominent numeric metrics with associated descriptive labels and optional delta/sentiment indicators.
_Avoid_: Stat tiles, number boxes
