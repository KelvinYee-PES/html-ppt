/**
 * Wire types for the htmlppt API.
 *
 * Slide element types mirror `backend/htmlppt/layout/model.py`. Elements are a
 * discriminated union on `kind`, so renderers can switch exhaustively.
 * Coordinates are EMU, font sizes are pt, colours are hex without `#`.
 */

// ---------------------------------------------------------------- Brand

export interface ThemeColors {
  dk1: string;
  lt1: string;
  dk2: string;
  lt2: string;
  accent1: string;
  accent2: string;
  accent3: string;
  accent4: string;
  accent5: string;
  accent6: string;
}

export interface ColorRoles {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  muted: string;
  on_primary: string;
  positive: string;
  negative: string;
  border: string;
}

interface FontSpec {
  family: string;
  fallback: string;
}

export interface BrandProfile {
  id: string;
  organization: string;
  name: string;
  colors: ThemeColors;
  roles: ColorRoles;
  chart_palette: string[];
  fonts: {
    heading: FontSpec;
    body: FontSpec;
    sizes: { title: number; subtitle: number; heading: number; body: number; caption: number; kpi: number };
  };
  slide_size: { width: number; height: number };
  design: {
    corner_radius: number;
    density: string;
    title_align: string;
    title_treatment: string;
    card_style: string;
    table_style: string;
    dark: boolean;
  };
  template?: {
    file_id: string;
    filename: string;
    layout_map: Record<string, string>;
    layouts: Array<{ name: string; placeholders: unknown[] }>;
  } | null;
  sources: Array<{ kind: string; filename: string; notes: string; confidence: Record<string, number> }>;
}

export interface PresetInfo {
  id: string;
  label: string;
  description: string;
}

export interface PaletteInfo {
  id: string;
  label: string;
  colors: string[];
}

// ---------------------------------------------------------------- Positioned slide model

export type Align = 'left' | 'center' | 'right' | 'justify';
export type VAlign = 'top' | 'middle' | 'bottom';

export interface TRun {
  text: string;
  font: string;
  size: number;
  color: string;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  strike: boolean;
  href: string | null;
  sup: boolean;
  sub: boolean;
}

export interface Para {
  runs: TRun[];
  level: number;
  bullet: string | null;
  bullet_color: string | null;
  align: Align;
  space_before: number;
  space_after: number;
  line_spacing: number;
}

interface ElementBase {
  x: number;
  y: number;
  w: number;
  h: number;
  name: string;
}

export interface TextEl extends ElementBase {
  kind: 'text';
  paras: Para[];
  valign: VAlign;
  inset: number;
  placeholder: 'title' | 'subtitle' | 'body' | null;
  fill: string | null;
  wrap: boolean;
}

export type ShapeGeom = 'rect' | 'roundRect' | 'ellipse' | 'line' | 'triangle' | 'chevron' | 'homePlate';

export interface ShapeEl extends ElementBase {
  kind: 'shape';
  geom: ShapeGeom;
  fill: string | null;
  fill_alpha: number;
  gradient: string[] | null;
  gradient_angle: number;
  line: string | null;
  line_w: number;
  dash: boolean;
  radius: number;
  shadow: boolean;
  paras: Para[] | null;
  valign: VAlign;
  inset: number;
  flip_v: boolean;
}

export interface CellEl {
  paras: Para[];
  fill: string | null;
  colspan: number;
  rowspan: number;
  merged: boolean;
  border_bottom: string | null;
  border_bottom_w: number;
  border_top: string | null;
  border_top_w: number;
  valign: VAlign;
}

export interface TableEl extends ElementBase {
  kind: 'table';
  col_widths: number[];
  row_heights: number[];
  rows: CellEl[][];
  margin: number;
}

export type ChartType = 'bar' | 'line' | 'area' | 'pie' | 'doughnut' | 'scatter' | 'radar';

export interface ChartSeries {
  name: string;
  values: Array<number | null>;
}

export interface ChartSpec {
  type: ChartType;
  horizontal: boolean;
  stacked: boolean;
  title: string;
  categories: string[];
  series: ChartSeries[];
  show_legend: boolean;
}

export interface ChartEl extends ElementBase {
  kind: 'chart';
  spec: ChartSpec;
  palette: string[];
  font: string;
  font_size: number;
  text_color: string;
  grid_color: string;
  legend: boolean;
  data_labels: boolean;
  title: boolean;
}

export interface ImageEl extends ElementBase {
  kind: 'image';
  mime: string;
  b64: string;
}

export interface SvgEl extends ElementBase {
  kind: 'svg';
  svg: string;
  recolor: string | null;
}

export interface GroupEl extends ElementBase {
  kind: 'group';
  children: SlideElement[];
}

export type SlideElement = TextEl | ShapeEl | TableEl | ChartEl | ImageEl | SvgEl | GroupEl;

export interface SlideModel {
  id: string;
  archetype: string;
  template_layout: string;
  background: string | null;
  elements: SlideElement[];
  notes: string;
  show_footer: boolean;
  number: number;
}

export interface DeckModel {
  width: number;
  height: number;
  slides: SlideModel[];
  fonts: string[];
}

// ---------------------------------------------------------------- Jobs

export interface JobCreated {
  job_id: string;
  slide_count: number;
  deck_model: DeckModel;
  warnings: string[];
}

export interface JobUpdated {
  status: 'updated';
  slide_count: number;
  deck_model: DeckModel;
}

export interface SlideUpdate {
  delete_indices?: number[];
  reorder_indices?: number[];
  /** slide id → archetype, or `'auto'` to clear the override. */
  layout_overrides?: Record<string, string>;
}
