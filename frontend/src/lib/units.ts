/** Unit helpers for rendering EMU-based slide models in the browser. */

export const EMU_PER_PT = 12700;

/** Normalise a backend hex colour (with or without `#`) to CSS. */
export function hex(color: string | null | undefined, fallback = 'transparent'): string {
  if (!color) return fallback;
  return `#${color.replace(/^#/, '')}`;
}

/** Hex colour with alpha (0..1) as CSS rgba(). */
export function hexAlpha(color: string, alpha: number): string {
  const c = color.replace(/^#/, '');
  if (alpha >= 1 || c.length !== 6) return `#${c}`;
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(c.slice(i, i + 2), 16));
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Converts EMU lengths to CSS `cqw` units relative to the slide width, so a
 * slide renders identically at any thumbnail size (the slide frame is a
 * size container).
 */
export function makeScale(deckWidth: number) {
  const perEmu = 100 / deckWidth;
  return {
    emu: (v: number) => `${v * perEmu}cqw`,
    pt: (v: number) => `${v * EMU_PER_PT * perEmu}cqw`,
  };
}

export type Scale = ReturnType<typeof makeScale>;

/** Accepts "1E40AF", "#1e40af" or "1e4" → "1E40AF"; null if not a colour. */
export function parseHex(input: string): string | null {
  let c = input.trim().replace(/^#/, '');
  if (/^[0-9a-f]{3}$/i.test(c)) c = [...c].map((ch) => ch + ch).join('');
  return /^[0-9a-f]{6}$/i.test(c) ? c.toUpperCase() : null;
}
