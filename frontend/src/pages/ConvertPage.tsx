import React, { useState, useEffect } from 'react';
import {
  Download,
  FileCode,
  Play,
  RefreshCw,
  UploadCloud,
  Moon,
  Sun,
  AlertCircle,
  Info,
  CheckCircle2,
} from 'lucide-react';
import type { BrandProfile, DeckModel, PaletteInfo, PresetInfo } from '../types';
import {
  createConversionJob,
  errorText,
  fetchBrands,
  fetchPalettes,
  fetchPresets,
  pptxDownloadUrl,
  updateJobSlides,
} from '../api/client';
import { PresetPicker } from '../components/PresetPicker';
import { SlideGrid } from '../components/SlideGrid';

const SAMPLE_EXECUTIVE = `<!DOCTYPE html>
<html>
<head><title>Executive Strategy Review 2027</title></head>
<body>
  <section class="slide">
    <h1>Executive Strategy 2027</h1>
    <p>Global Leadership Summit · Frankfurt</p>
  </section>

  <section class="slide">
    <h2>Performance Highlights</h2>
    <div style="display:flex;gap:24px;">
      <div><span style="font-size:36px;font-weight:bold">€128M</span><p>Annual Revenue (+24% YoY)</p></div>
      <div><span style="font-size:36px;font-weight:bold">34.2%</span><p>Operating Gross Margin</p></div>
      <div><span style="font-size:36px;font-weight:bold">99.95%</span><p>Enterprise SLA Reliability</p></div>
    </div>
    <ul>
      <li>Accelerated cloud migration program ahead of Q3 deadline across 14 data centers</li>
      <li>Expanded partner channels across tier-1 regional automotive and financial hubs</li>
      <li>Secured ISO 26262 ASIL-D safety certifications for autonomous controller stack</li>
    </ul>
  </section>
</body>
</html>`;

const SAMPLE_FINANCIAL = `<!DOCTYPE html>
<html>
<head><title>Quarterly Technology & Infrastructure Review</title></head>
<body>
  <section class="slide">
    <h1>Infrastructure & Platform Growth</h1>
    <p>Engineering & Operations Executive Committee</p>
  </section>

  <section class="slide">
    <h2>Quarterly Cluster Utilization</h2>
    <table>
      <thead>
        <tr><th>Region</th><th>Active Compute</th><th>Storage (PB)</th><th>Cost / FLOP</th></tr>
      </thead>
      <tbody>
        <tr><td>Europe North</td><td>4,200 Nodes</td><td>12.4</td><td>€0.014</td></tr>
        <tr><td>US East</td><td>8,150 Nodes</td><td>24.8</td><td>€0.012</td></tr>
        <tr><td>APAC Tokyo</td><td>3,400 Nodes</td><td>9.6</td><td>€0.015</td></tr>
      </tbody>
    </table>
    <ul>
      <li>Overall carbon intensity decreased 18% following geothermal data center switch</li>
      <li>Automated scale-down logic reduced off-peak cluster overhead by €420k monthly</li>
    </ul>
  </section>
</body>
</html>`;

export const ConvertPage: React.FC = () => {
  const [htmlInputMode, setHtmlInputMode] = useState<'paste' | 'upload'>('paste');
  const [htmlText, setHtmlText] = useState<string>(SAMPLE_EXECUTIVE);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [presets, setPresets] = useState<PresetInfo[]>([]);
  const [palettes, setPalettes] = useState<PaletteInfo[]>([]);
  const [brands, setBrands] = useState<BrandProfile[]>([]);

  const [selectedPreset, setSelectedPreset] = useState<string>('corporate');
  const [selectedBrandId, setSelectedBrandId] = useState<string>('');
  const [selectedPalette, setSelectedPalette] = useState<string>('ocean');
  const [darkMode, setDarkMode] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [deckModel, setDeckModel] = useState<DeckModel | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([fetchPresets(), fetchPalettes(), fetchBrands()])
      .then(([pr, pa, br]) => {
        if (!active) return;
        setPresets(pr);
        setPalettes(pa);
        setBrands(br);
      })
      .catch((err) => {
        if (active) setError(errorText(err));
      });

    return () => {
      active = false;
    };
  }, []);

  const handleConvert = async () => {
    if (htmlInputMode === 'paste' && !htmlText.trim()) {
      setError('Please provide HTML content before converting.');
      return;
    }
    if (htmlInputMode === 'upload' && !selectedFile) {
      setError('Please select an HTML file to upload.');
      return;
    }

    setLoading(true);
    setError(null);
    setWarnings([]);

    try {
      const source =
        htmlInputMode === 'upload' && selectedFile
          ? { kind: 'file' as const, file: selectedFile }
          : { kind: 'paste' as const, html: htmlText };

      const res = await createConversionJob({
        source,
        brandId: selectedBrandId ? selectedBrandId : null,
        palette: selectedPalette,
        preset: selectedPreset,
        dark: darkMode,
      });

      setCurrentJobId(res.job_id);
      setDeckModel(res.deck_model);
      if (res.warnings && res.warnings.length > 0) {
        setWarnings(res.warnings);
      }
    } catch (err: unknown) {
      setError(errorText(err));
    } finally {
      setLoading(false);
    }
  };

  const handleMoveSlide = async (fromIdx: number, toIdx: number) => {
    if (!currentJobId || !deckModel) return;
    const indices = deckModel.slides.map((_, i) => i);
    const [moved] = indices.splice(fromIdx, 1);
    indices.splice(toIdx, 0, moved);

    try {
      const res = await updateJobSlides(currentJobId, { reorder_indices: indices });
      setDeckModel(res.deck_model);
    } catch (err: unknown) {
      setError(errorText(err));
    }
  };

  const handleDeleteSlide = async (idx: number) => {
    if (!currentJobId || !deckModel) return;
    if (deckModel.slides.length <= 1) {
      setError('The presentation must have at least one slide.');
      return;
    }

    try {
      const res = await updateJobSlides(currentJobId, { delete_indices: [idx] });
      setDeckModel(res.deck_model);
    } catch (err: unknown) {
      setError(errorText(err));
    }
  };

  const handleChangeLayout = async (slideId: string, layout: string) => {
    if (!currentJobId || !deckModel) return;
    try {
      const res = await updateJobSlides(currentJobId, {
        layout_overrides: { [slideId]: layout },
      });
      setDeckModel(res.deck_model);
    } catch (err: unknown) {
      setError(errorText(err));
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col gap-10">
      {/* Studio Header & Introduction */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--color-rule)]">
        <div>
          <h1 className="text-2xl font-display font-bold text-slate-900 tracking-tight">
            HTML to PowerPoint Compiler
          </h1>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
            Recreates AI-generated HTML reports and slide layouts into native, fully editable PowerPoint shapes, vector graphics, charts, and data tables.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setDarkMode(!darkMode)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg border text-xs font-semibold transition ${
              darkMode
                ? 'bg-slate-900 border-slate-900 text-white shadow-xs'
                : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
            }`}
          >
            {darkMode ? <Moon className="w-3.5 h-3.5 text-blue-300" /> : <Sun className="w-3.5 h-3.5 text-amber-500" />}
            {darkMode ? 'Dark Slide Canvas' : 'Light Slide Canvas'}
          </button>
        </div>
      </div>

      {/* Compiler Workbench Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (7 cols): HTML Input Panel */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-[var(--color-rule)] p-6 shadow-sm flex flex-col gap-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                1
              </span>
              <span className="font-semibold text-sm text-slate-900">Source HTML</span>
            </div>

            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
              <button
                type="button"
                onClick={() => setHtmlInputMode('paste')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                  htmlInputMode === 'paste' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <FileCode className="w-3.5 h-3.5 inline mr-1 text-[var(--color-proof)]" /> Paste
              </button>
              <button
                type="button"
                onClick={() => setHtmlInputMode('upload')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                  htmlInputMode === 'upload' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <UploadCloud className="w-3.5 h-3.5 inline mr-1 text-slate-600" /> Upload File
              </button>
            </div>
          </div>

          {htmlInputMode === 'paste' ? (
            <div className="flex flex-col gap-2.5">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Enter HTML document with slides or sections</span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setHtmlText(SAMPLE_EXECUTIVE)}
                    className="text-[11px] text-[var(--color-proof)] hover:underline font-medium"
                  >
                    Sample: Executive
                  </button>
                  <span className="text-slate-300">·</span>
                  <button
                    type="button"
                    onClick={() => setHtmlText(SAMPLE_FINANCIAL)}
                    className="text-[11px] text-[var(--color-proof)] hover:underline font-medium"
                  >
                    Sample: Financial
                  </button>
                </div>
              </div>

              <textarea
                rows={12}
                value={htmlText}
                onChange={(e) => setHtmlText(e.target.value)}
                placeholder="Paste AI-generated HTML content here..."
                className="w-full bg-slate-50 font-mono text-xs text-slate-800 p-4 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-proof)] focus:bg-white transition leading-relaxed"
                spellCheck={false}
              />

              <div className="flex justify-between items-center text-[11px] text-slate-400 font-mono">
                <span>{htmlText.length.toLocaleString()} characters</span>
                <span>{htmlText.split('\n').length} lines</span>
              </div>
            </div>
          ) : (
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-10 text-center bg-slate-50 hover:bg-slate-100/70 hover:border-slate-400 transition flex flex-col items-center justify-center">
              <input
                type="file"
                accept=".html,.htm"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="hidden"
                id="html-file-upload"
              />
              <label htmlFor="html-file-upload" className="cursor-pointer flex flex-col items-center gap-2.5">
                <div className="w-12 h-12 rounded-xl bg-slate-200/80 flex items-center justify-center text-slate-700">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <span className="text-sm font-semibold text-slate-800">
                  {selectedFile ? selectedFile.name : 'Choose an HTML file or drag & drop here'}
                </span>
                <span className="text-xs text-slate-500">
                  {selectedFile
                    ? `${(selectedFile.size / 1024).toFixed(1)} KB · Click to replace`
                    : 'Supports full reports, slide decks, and rich dashboard exports'}
                </span>
              </label>
            </div>
          )}
        </div>

        {/* Right Column (5 cols): Design Language & Action Panel */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div className="bg-white rounded-2xl border border-[var(--color-rule)] p-6 shadow-sm flex flex-col gap-5">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                2
              </span>
              <span className="font-semibold text-sm text-slate-900">Brand & Style Guidelines</span>
            </div>

            {/* Corporate Brand Selection */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-slate-700">
                Corporate Design / Brand Profile
              </label>
              <select
                value={selectedBrandId}
                onChange={(e) => setSelectedBrandId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 text-slate-800 text-xs rounded-xl px-3.5 py-2.5 focus:ring-2 focus:ring-[var(--color-proof)] focus:bg-white focus:outline-none transition cursor-pointer"
              >
                <option value="">Curated Palette (Standard)</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} — {b.organization}
                  </option>
                ))}
              </select>
            </div>

            {/* Curated Palette Picker */}
            {!selectedBrandId && (
              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-slate-700">
                  Palette Swatches
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {palettes.map((pal) => {
                    const isSelected = selectedPalette === pal.id;
                    return (
                      <button
                        key={pal.id}
                        type="button"
                        onClick={() => setSelectedPalette(pal.id)}
                        className={`p-2 rounded-xl border flex flex-col items-center gap-1.5 transition text-left ${
                          isSelected
                            ? 'border-[var(--color-proof)] bg-[var(--color-proof-soft)]/40 ring-1 ring-[var(--color-proof)]'
                            : 'border-slate-200 bg-slate-50 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex gap-1">
                          {pal.colors.slice(0, 3).map((c, ci) => (
                            <div
                              key={ci}
                              className="w-3 h-3 rounded-full border border-black/10"
                              style={{ backgroundColor: `#${c}` }}
                            />
                          ))}
                        </div>
                        <span className="text-[11px] font-medium text-slate-700 truncate max-w-full">
                          {pal.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Convert Trigger */}
            <div className="pt-2">
              <button
                type="button"
                disabled={loading}
                onClick={handleConvert}
                className="w-full relative overflow-hidden flex items-center justify-center gap-2.5 bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-white px-6 py-3 rounded-xl font-semibold text-sm shadow-md hover:shadow-lg transition-all disabled:opacity-50 cursor-pointer"
              >
                {loading && <div className="progress-line" />}
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-rose-400" />
                    <span>Rendering DOM & Compiling Native PPTX...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Compile to PowerPoint (.pptx)</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Presets Row */}
          <div className="bg-white rounded-2xl border border-[var(--color-rule)] p-6 shadow-sm flex flex-col gap-4">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                3
              </span>
              <span className="font-semibold text-sm text-slate-900">Layout Preset Archetype</span>
            </div>

            <PresetPicker
              presets={presets}
              selectedPreset={selectedPreset}
              onSelect={setSelectedPreset}
            />
          </div>
        </div>
      </div>

      {/* Errors or Warnings */}
      {error && (
        <div className="p-4 bg-[var(--color-danger-soft)] border border-[var(--color-danger)]/30 rounded-xl text-[var(--color-danger)] text-xs flex items-start gap-3 shadow-xs">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold block mb-0.5">Conversion error</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs flex items-start gap-3">
          <Info className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
          <div>
            <span className="font-bold block mb-0.5">Pipeline segmentation notices</span>
            <ul className="list-disc list-inside space-y-0.5 text-amber-700">
              {warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Slide Deck Studio Preview Section */}
      {deckModel && (
        <div className="flex flex-col gap-6 pt-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-[var(--color-rule)] p-5 rounded-2xl shadow-sm">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-display font-bold text-slate-900">
                  PowerPoint Presentation Proof ({deckModel.slides.length} slides)
                </h2>
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-0.5 font-mono">
                  <span>Aspect: 16:9 Widescreen</span>
                  <span>·</span>
                  <span>{deckModel.fonts.filter(Boolean).join(', ') || 'Calibri'}</span>
                  <span>·</span>
                  <span>All shapes native vector</span>
                </div>
              </div>
            </div>

            {currentJobId && (
              <a
                href={pptxDownloadUrl(currentJobId)}
                download
                className="flex items-center justify-center gap-2 bg-emerald-700 hover:bg-emerald-600 active:bg-emerald-800 text-white px-5 py-2.5 rounded-xl font-semibold text-xs shadow-sm hover:shadow transition"
              >
                <Download className="w-4 h-4" />
                Download Presentation (.pptx)
              </a>
            )}
          </div>

          <SlideGrid
            deckModel={deckModel}
            onMoveSlide={handleMoveSlide}
            onDeleteSlide={handleDeleteSlide}
            onChangeLayout={handleChangeLayout}
          />
        </div>
      )}
    </div>
  );
};
