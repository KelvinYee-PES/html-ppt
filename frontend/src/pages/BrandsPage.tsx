import React, { useState, useEffect, useCallback } from 'react';
import {
  Upload,
  Trash2,
  Download,
  Sparkles,
  ShieldCheck,
  AlertCircle,
  PackageOpen,
  X,
  RefreshCw,
} from 'lucide-react';
import type { BrandProfile } from '../types';
import {
  analyzeDecks,
  brandExportUrl,
  deleteBrand,
  errorText,
  extractTemplate,
  fetchBrands,
  importBrand,
  saveBrand,
} from '../api/client';
import { hex } from '../lib/units';

export const BrandsPage: React.FC = () => {
  const [brands, setBrands] = useState<BrandProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewBrand, setReviewBrand] = useState<BrandProfile | null>(null);

  const loadBrands = useCallback(async () => {
    try {
      const data = await fetchBrands();
      setBrands(data);
    } catch (err: unknown) {
      setError(errorText(err));
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    fetchBrands()
      .then((data) => {
        if (!ignore) setBrands(data);
      })
      .catch((err: unknown) => {
        if (!ignore) setError(errorText(err));
      });

    return () => {
      ignore = true;
    };
  }, []);

  const handleTemplateUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setStatusMessage(`Extracting slide master, color schemes, and font styles from "${file.name}"...`);
    setError(null);
    try {
      const brand = await extractTemplate(file);
      setReviewBrand(brand);
      await loadBrands();
    } catch (err: unknown) {
      setError(errorText(err));
    } finally {
      setLoading(false);
      setStatusMessage(null);
      e.target.value = '';
    }
  };

  const handleDecksUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || !files.length) return;
    setLoading(true);
    setStatusMessage(`Inferring corporate design language statistically from ${files.length} decks...`);
    setError(null);
    try {
      const brand = await analyzeDecks(Array.from(files));
      setReviewBrand(brand);
      await loadBrands();
    } catch (err: unknown) {
      setError(errorText(err));
    } finally {
      setLoading(false);
      setStatusMessage(null);
      e.target.value = '';
    }
  };

  const handleImportBrand = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setStatusMessage(`Importing brand bundle package "${file.name}"...`);
    setError(null);
    try {
      const brand = await importBrand(file);
      setReviewBrand(brand);
      await loadBrands();
    } catch (err: unknown) {
      setError(errorText(err));
    } finally {
      setLoading(false);
      setStatusMessage(null);
      e.target.value = '';
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete brand profile "${name}"?`)) return;
    try {
      await deleteBrand(id);
      await loadBrands();
    } catch (err: unknown) {
      setError(errorText(err));
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col gap-10">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--color-rule)]">
        <div>
          <h1 className="text-2xl font-display font-bold text-slate-900 tracking-tight">
            Brand Profiles & Corporate Design
          </h1>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
            Extract color themes, typography pairings, slide masters, and layouts directly from your organization's .pptx or .potx templates.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Upload Template */}
          <label className="cursor-pointer flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-4 py-2.5 rounded-xl text-xs font-semibold shadow-xs transition">
            <Upload className="w-4 h-4 text-rose-400" />
            Upload Template (.potx / .pptx)
            <input
              type="file"
              accept=".pptx,.potx"
              onChange={handleTemplateUpload}
              className="hidden"
            />
          </label>

          {/* Analyze Past Decks */}
          <label className="cursor-pointer flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-xs transition">
            <Sparkles className="w-4 h-4 text-amber-500" />
            Analyze Past Decks
            <input
              type="file"
              multiple
              accept=".pptx"
              onChange={handleDecksUpload}
              className="hidden"
            />
          </label>

          {/* Import Package */}
          <label className="cursor-pointer flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 px-3 py-2.5 rounded-xl text-xs font-semibold shadow-xs transition" title="Import exported .htmlppt-brand package">
            <PackageOpen className="w-4 h-4 text-slate-600" />
            Import Package
            <input
              type="file"
              accept=".htmlppt-brand,.zip"
              onChange={handleImportBrand}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Progress & Notifications */}
      {loading && (
        <div className="p-4 bg-white border border-[var(--color-rule)] rounded-2xl shadow-xs text-xs flex items-center gap-3 text-slate-700">
          <RefreshCw className="w-4 h-4 animate-spin text-[var(--color-proof)]" />
          <span>{statusMessage || 'Processing brand profile data...'}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-[var(--color-danger-soft)] border border-[var(--color-danger)]/30 rounded-xl text-[var(--color-danger)] text-xs flex items-start gap-3 shadow-xs">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold block mb-0.5">Error processing brand</span>
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-slate-400 hover:text-slate-700 p-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* Brand Profiles Grid */}
      {brands.length === 0 && !loading ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center flex flex-col items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-500">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="font-display font-semibold text-base text-slate-900">
            No Custom Brand Profiles Yet
          </h3>
          <p className="text-xs text-slate-500 max-w-md leading-relaxed">
            Upload your organization's corporate PowerPoint template or a set of representative slides. The engine automatically maps shapes, color roles, and font rules.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {brands.map((b) => (
            <div
              key={b.id}
              className="bg-white border border-[var(--color-rule)] rounded-2xl p-5 flex flex-col justify-between gap-5 shadow-sm hover:shadow-md hover:border-slate-300 transition"
            >
              <div className="flex flex-col gap-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-display font-bold text-base text-slate-900 leading-snug">
                      {b.name}
                    </h3>
                    <span className="text-xs text-slate-500 font-mono mt-0.5 block">
                      {b.organization || 'Corporate Profile'}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDelete(b.id, b.name)}
                    className="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition"
                    title="Delete brand profile"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Theme Palette Swatches */}
                <div className="flex items-center gap-1.5 py-1">
                  {[b.colors.accent1, b.colors.accent2, b.colors.accent3, b.colors.accent4, b.colors.dk1, b.colors.lt1]
                    .filter(Boolean)
                    .map((c, i) => (
                      <div
                        key={i}
                        className="w-6 h-6 rounded-lg border border-slate-200/80 shadow-2xs transition hover:scale-110"
                        style={{ backgroundColor: hex(c) }}
                        title={`#${c}`}
                      />
                    ))}
                </div>

                {/* Fonts & Master Info */}
                <div className="text-xs text-slate-600 flex flex-col gap-1.5 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Headings:</span>
                    <span className="font-semibold text-slate-800 truncate max-w-[160px]">
                      {b.fonts.heading.family}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Body:</span>
                    <span className="font-semibold text-slate-800 truncate max-w-[160px]">
                      {b.fonts.body.family}
                    </span>
                  </div>
                  {b.template?.filename && (
                    <div className="flex justify-between items-center pt-1 border-t border-slate-200/80 text-[11px]">
                      <span className="text-slate-500">Template Base:</span>
                      <span className="text-[var(--color-proof)] font-mono truncate max-w-[160px]" title={b.template.filename}>
                        {b.template.filename}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setReviewBrand(b)}
                  className="text-xs font-semibold text-[var(--color-proof)] hover:underline"
                >
                  Inspect & Edit Profile
                </button>
                <a
                  href={brandExportUrl(b.id)}
                  download
                  className="text-xs font-medium text-slate-600 hover:text-slate-900 flex items-center gap-1.5 px-2.5 py-1 rounded-lg hover:bg-slate-100 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export</span>
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review & Edit Brand Modal */}
      {reviewBrand && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 sm:p-6"
          onClick={() => setReviewBrand(null)}
        >
          <div
            className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 shadow-2xl flex flex-col gap-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h2 className="font-display font-bold text-base text-slate-900">
                Inspect Corporate Design Profile
              </h2>
              <button
                type="button"
                onClick={() => setReviewBrand(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-col gap-4 text-xs text-slate-700 max-h-[65vh] overflow-y-auto pr-1">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Brand / Profile Name</label>
                <input
                  type="text"
                  value={reviewBrand.name}
                  onChange={(e) => setReviewBrand({ ...reviewBrand, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-800 text-xs focus:ring-1 focus:ring-[var(--color-proof)] focus:bg-white focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Organization</label>
                <input
                  type="text"
                  value={reviewBrand.organization}
                  onChange={(e) => setReviewBrand({ ...reviewBrand, organization: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-800 text-xs focus:ring-1 focus:ring-[var(--color-proof)] focus:bg-white focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Primary Color (Hex)</label>
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={reviewBrand.roles.primary}
                    onChange={(e) =>
                      setReviewBrand({
                        ...reviewBrand,
                        roles: { ...reviewBrand.roles, primary: e.target.value.replace('#', '') },
                        colors: { ...reviewBrand.colors, accent1: e.target.value.replace('#', '') },
                      })
                    }
                    className="w-32 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-800 text-xs font-mono uppercase focus:ring-1 focus:ring-[var(--color-proof)] focus:bg-white focus:outline-none"
                  />
                  <div
                    className="w-8 h-8 rounded-lg border border-slate-300 shadow-2xs"
                    style={{ backgroundColor: hex(reviewBrand.roles.primary) }}
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Heading Font Family</label>
                <input
                  type="text"
                  value={reviewBrand.fonts.heading.family}
                  onChange={(e) =>
                    setReviewBrand({
                      ...reviewBrand,
                      fonts: {
                        ...reviewBrand.fonts,
                        heading: { ...reviewBrand.fonts.heading, family: e.target.value },
                      },
                    })
                  }
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-800 text-xs focus:ring-1 focus:ring-[var(--color-proof)] focus:bg-white focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Body Font Family</label>
                <input
                  type="text"
                  value={reviewBrand.fonts.body.family}
                  onChange={(e) =>
                    setReviewBrand({
                      ...reviewBrand,
                      fonts: {
                        ...reviewBrand.fonts,
                        body: { ...reviewBrand.fonts.body, family: e.target.value },
                      },
                    })
                  }
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-800 text-xs focus:ring-1 focus:ring-[var(--color-proof)] focus:bg-white focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setReviewBrand(null)}
                className="px-4 py-2 rounded-xl text-slate-600 hover:text-slate-900 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    await saveBrand(reviewBrand);
                    setReviewBrand(null);
                    await loadBrands();
                  } catch (err: unknown) {
                    setError(errorText(err));
                  }
                }}
                className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-xs cursor-pointer"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
