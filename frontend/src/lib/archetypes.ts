/** Layout archetypes accepted by `PATCH /api/jobs/:id/slides` (see backend LAYOUT_ARCHETYPES). */
export const ARCHETYPES = [
  { id: 'bullets', label: 'Text and bullets' },
  { id: 'two_column', label: 'Two columns' },
  { id: 'kpi_grid', label: 'KPI tiles' },
  { id: 'chart_focus', label: 'Chart' },
  { id: 'chart_plus_text', label: 'Chart with text' },
  { id: 'table', label: 'Table' },
  { id: 'cards', label: 'Cards' },
  { id: 'quote', label: 'Quote' },
  { id: 'title', label: 'Title' },
  { id: 'section', label: 'Section divider' },
  { id: 'closing', label: 'Closing' },
  { id: 'freeform', label: 'Original positions' },
  { id: 'blank', label: 'Blank' },
] as const;

export type Archetype = (typeof ARCHETYPES)[number]['id'];

export function isArchetype(value: string): value is Archetype {
  return ARCHETYPES.some((a) => a.id === value);
}

export function archetypeLabel(id: string): string {
  return ARCHETYPES.find((a) => a.id === id)?.label ?? id;
}
