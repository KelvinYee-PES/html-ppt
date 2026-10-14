import type {
  BrandProfile,
  JobCreated,
  JobUpdated,
  PaletteInfo,
  PresetInfo,
  SlideUpdate,
} from '../types';

/**
 * Empty by default so requests are same-origin: the Vite dev server proxies
 * `/api` to FastAPI, and in production FastAPI serves the built frontend.
 */
const API_BASE: string = import.meta.env.VITE_API_BASE ?? '';

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(0, 'Can’t reach the conversion server. Check that the backend is running on port 8000.');
  }
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res));
  return (await res.json()) as T;
}

async function errorMessage(res: Response): Promise<string> {
  const text = await res.text().catch(() => '');
  try {
    const body: unknown = JSON.parse(text);
    if (body && typeof body === 'object' && 'detail' in body) {
      const { detail } = body as { detail: unknown };
      if (typeof detail === 'string') return detail;
      // FastAPI validation errors: [{ msg, loc }]
      if (Array.isArray(detail)) {
        return detail
          .map((d) => (d && typeof d === 'object' && 'msg' in d ? String(d.msg) : String(d)))
          .join('; ');
      }
    }
  } catch {
    /* not JSON */
  }
  return text || `Request failed (${res.status} ${res.statusText})`;
}

export function errorText(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

// ---------------------------------------------------------------- Catalog

export const fetchPresets = () => request<PresetInfo[]>('/api/presets');
export const fetchPalettes = () => request<PaletteInfo[]>('/api/palettes');

// ---------------------------------------------------------------- Brands

export const fetchBrands = () => request<BrandProfile[]>('/api/brands');
export const saveBrand = (brand: BrandProfile) => request<BrandProfile>('/api/brands', json('POST', brand));
export const deleteBrand = (id: string) =>
  request<{ status: string }>(`/api/brands/${encodeURIComponent(id)}`, { method: 'DELETE' });

export function extractTemplate(file: File): Promise<BrandProfile> {
  const body = new FormData();
  body.append('file', file);
  return request<BrandProfile>('/api/brands/extract-template', { method: 'POST', body });
}

export function analyzeDecks(files: readonly File[]): Promise<BrandProfile> {
  const body = new FormData();
  for (const f of files) body.append('files', f);
  return request<BrandProfile>('/api/brands/analyze-decks', { method: 'POST', body });
}

export function importBrand(file: File): Promise<BrandProfile> {
  const body = new FormData();
  body.append('file', file);
  return request<BrandProfile>('/api/brands/import', { method: 'POST', body });
}

export const brandExportUrl = (id: string) => `${API_BASE}/api/brands/${encodeURIComponent(id)}/export`;

// ---------------------------------------------------------------- Jobs

export type HtmlSource = { kind: 'paste'; html: string } | { kind: 'file'; file: File };

export interface ConvertOptions {
  source: HtmlSource;
  brandId: string | null;
  palette: string;
  preset: string;
  dark: boolean;
}

export function createConversionJob(opts: ConvertOptions): Promise<JobCreated> {
  const body = new FormData();
  if (opts.source.kind === 'file') body.append('html_file', opts.source.file);
  else body.append('html_content', opts.source.html);
  if (opts.brandId) body.append('brand_id', opts.brandId);
  body.append('palette', opts.palette);
  body.append('preset', opts.preset);
  body.append('dark', String(opts.dark));
  return request<JobCreated>('/api/jobs', { method: 'POST', body });
}

export const updateJobSlides = (jobId: string, update: SlideUpdate) =>
  request<JobUpdated>(`/api/jobs/${encodeURIComponent(jobId)}/slides`, json('PATCH', update));

export const pptxDownloadUrl = (jobId: string) => `${API_BASE}/api/jobs/${encodeURIComponent(jobId)}/pptx`;
