# ADR 0001: Archetype Layout Elegance and Dynamic Dark-Mode Contrast

## Status
Accepted

## Context
When converting modern HTML decks (e.g. `ai_automotive_motor_ecu_v_cycle.html`) into PPTX, the layout engine defaulted to rigid geometric assumptions:
1. `_make_dark` reused raw palette `accent1` (often deep navy like `#1D4ED8`) for `roles.primary`, resulting in nearly 1:1 illegible contrast against dark navy surfaces.
2. `CardGrid` stretched all cards to 100% of the content height (`tile_h = cr.h`) and forced all cards into a single row, creating 4 tall, squished vertical columns.
3. `KPIGroup` allocated 75% of slide height, creating massive empty vertical capsules.
4. `two_column` naively divided blocks without checking balance, leaving empty voids on one side.

## Decisions

1. **Luminous Dark-Mode Accents**: In dark mode, role derivations must ensure all text and primary accents meet WCAG AA (>= 4.5:1) contrast against backgrounds and surfaces. Deep accents are lightened to luminous counterparts (e.g., `#38BDF8` / `#60A5FA`).
2. **Adaptive CardGrid Wrapping**: `CardGrid` layouts with 4 items must wrap into a 2×2 grid; 5-6 items must wrap into 2×3. Card heights must be sized to content budget with breathing room rather than stretching to the slide footer.
3. **Proportional KPI Metrics**: KPI tiles have a bounded height budget (max 35% slide content height) and are vertically balanced.
4. **Content-Aware Two-Column Balancing**: When one column is empty or contains fewer than 15% of the slide's visual content, the layout collapses into a centered/full-width card rather than exposing an empty half-screen.

## Consequences
- Slide previews and exported PPTX will maintain high contrast and modern card geometry across both light and dark modes.
- Archetype layout algorithms in `engine.py` become responsive to item count and content volume.
