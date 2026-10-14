import React, { useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Trash2,
  Maximize2,
  X,
  Layers,
  ArrowUpDown,
} from 'lucide-react';
import type { DeckModel, SlideModel } from '../types';
import { ARCHETYPES } from '../lib/archetypes';
import { SlidePreview } from './SlidePreview';

interface SlideGridProps {
  deckModel: DeckModel;
  onMoveSlide: (fromIdx: number, toIdx: number) => void;
  onDeleteSlide: (idx: number) => void;
  onChangeLayout: (slideId: string, layout: string) => void;
}

export const SlideGrid: React.FC<SlideGridProps> = ({
  deckModel,
  onMoveSlide,
  onDeleteSlide,
  onChangeLayout,
}) => {
  const [inspectIndex, setInspectIndex] = useState<number | null>(null);

  const activeInspectSlide: SlideModel | null =
    inspectIndex !== null && deckModel.slides[inspectIndex] ? deckModel.slides[inspectIndex] : null;

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {deckModel.slides.map((slide, idx) => {
          const isFirst = idx === 0;
          const isLast = idx === deckModel.slides.length - 1;
          const canDelete = deckModel.slides.length > 1;

          return (
            <div
              key={slide.id || idx}
              className="bg-white rounded-xl border border-[var(--color-rule)] hover:border-[var(--color-rule-soft)] shadow-sm hover:shadow-md transition-all flex flex-col justify-between overflow-hidden group"
            >
              {/* Header Bar */}
              <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-[var(--color-rule-soft)] bg-slate-50/70">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-200/80 text-slate-700">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="text-xs font-medium text-slate-500 truncate max-w-[120px]">
                    {slide.archetype ? slide.archetype.replace('_', ' ') : 'slide'}
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setInspectIndex(idx)}
                    title="Zoom & Inspect Slide"
                    className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </button>

                  <button
                    type="button"
                    disabled={isFirst}
                    onClick={() => onMoveSlide(idx, idx - 1)}
                    title="Move previous"
                    className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 disabled:opacity-25 disabled:hover:bg-transparent transition"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    disabled={isLast}
                    onClick={() => onMoveSlide(idx, idx + 1)}
                    title="Move next"
                    className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 disabled:opacity-25 disabled:hover:bg-transparent transition"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    disabled={!canDelete}
                    onClick={() => onDeleteSlide(idx)}
                    title={canDelete ? 'Delete slide' : 'Deck must have at least one slide'}
                    className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 disabled:opacity-25 disabled:hover:bg-transparent transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Slide Canvas Thumbnail */}
              <div className="p-3 bg-slate-100/50">
                <div className="relative rounded-lg overflow-hidden border border-slate-200 shadow-sm transition hover:ring-2 hover:ring-[var(--color-proof)]/30">
                  <SlidePreview
                    slide={slide}
                    deckWidth={deckModel.width}
                    deckHeight={deckModel.height}
                    onClick={() => setInspectIndex(idx)}
                  />
                </div>
              </div>

              {/* Footer Controls: Layout Switcher */}
              <div className="px-3.5 py-2.5 border-t border-[var(--color-rule-soft)] bg-white flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5 text-slate-500 font-medium">
                  <Layers className="w-3.5 h-3.5 text-slate-400" />
                  <span>Layout</span>
                </div>

                <div className="relative">
                  <select
                    value={slide.archetype || 'bullets'}
                    onChange={(e) => onChangeLayout(slide.id, e.target.value)}
                    className="appearance-none bg-slate-50 hover:bg-slate-100 border border-slate-300 text-slate-700 text-xs rounded-md pl-2.5 pr-7 py-1 focus:ring-1 focus:ring-[var(--color-proof)] focus:border-[var(--color-proof)] focus:outline-none transition cursor-pointer"
                  >
                    {ARCHETYPES.map((arc) => (
                      <option key={arc.id} value={arc.id}>
                        {arc.label}
                      </option>
                    ))}
                  </select>
                  <ArrowUpDown className="w-3 h-3 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Slide Inspection Lightbox Modal */}
      {activeInspectSlide !== null && inspectIndex !== null && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/70 backdrop-blur-sm"
          onClick={() => setInspectIndex(null)}
        >
          <div
            className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-bold px-2.5 py-1 rounded-md bg-[var(--color-proof-soft)] text-[var(--color-proof)]">
                  Slide {inspectIndex + 1} of {deckModel.slides.length}
                </span>
                <span className="text-sm font-semibold text-slate-700">
                  {activeInspectSlide.archetype ? activeInspectSlide.archetype.replace('_', ' ') : 'Slide Preview'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={inspectIndex === 0}
                  onClick={() => setInspectIndex(inspectIndex - 1)}
                  className="p-1.5 rounded-lg border border-slate-300 hover:bg-white text-slate-600 disabled:opacity-30 disabled:hover:bg-transparent"
                  title="Previous slide"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  disabled={inspectIndex === deckModel.slides.length - 1}
                  onClick={() => setInspectIndex(inspectIndex + 1)}
                  className="p-1.5 rounded-lg border border-slate-300 hover:bg-white text-slate-600 disabled:opacity-30 disabled:hover:bg-transparent"
                  title="Next slide"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={() => setInspectIndex(null)}
                  className="p-1.5 rounded-lg hover:bg-slate-200/70 text-slate-500 hover:text-slate-700 ml-2"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body: Large Slide Preview with crop marks */}
            <div className="p-6 md:p-8 overflow-y-auto flex flex-col items-center justify-center bg-[var(--color-board)]/50 min-h-[380px]">
              <div className="w-full max-w-3xl rounded-xl overflow-hidden shadow-2xl border border-slate-300">
                <SlidePreview
                  slide={activeInspectSlide}
                  deckWidth={deckModel.width}
                  deckHeight={deckModel.height}
                />
              </div>

              {/* Elements & Notes Inspector */}
              <div className="w-full max-w-3xl mt-6 flex flex-col sm:flex-row gap-4 text-xs text-slate-600">
                <div className="flex-1 bg-white p-3.5 rounded-xl border border-slate-200">
                  <span className="font-semibold text-slate-800 block mb-1">Slide Details</span>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-slate-600 font-mono text-[11px]">
                    <span>Elements: {activeInspectSlide.elements.length}</span>
                    <span>Layout: {activeInspectSlide.archetype}</span>
                    <span>Slide #: {inspectIndex + 1}</span>
                  </div>
                </div>

                {activeInspectSlide.notes && (
                  <div className="flex-1 bg-white p-3.5 rounded-xl border border-slate-200">
                    <span className="font-semibold text-slate-800 block mb-1">Speaker Notes</span>
                    <p className="text-slate-600 italic line-clamp-3">{activeInspectSlide.notes}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
