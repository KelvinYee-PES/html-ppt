import React from 'react';
import type { PresetInfo } from '../types';

interface PresetPickerProps {
  presets: PresetInfo[];
  selectedPreset: string;
  onSelect: (id: string) => void;
}

export const PresetPicker: React.FC<PresetPickerProps> = ({
  presets,
  selectedPreset,
  onSelect,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
      {presets.map((p) => {
        const isSelected = selectedPreset === p.id;

        return (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelect(p.id)}
            aria-pressed={isSelected}
            className={`text-left p-3.5 rounded-xl border transition-all relative flex flex-col justify-between gap-3 ${
              isSelected
                ? 'border-[var(--color-proof)] bg-white ring-2 ring-[var(--color-proof-soft)] shadow-sm'
                : 'border-[var(--color-rule)] bg-white hover:border-slate-300 hover:shadow-xs'
            }`}
          >
            <div>
              {/* Preset Visual Archetype Miniature Icon */}
              <div className="h-9 mb-2.5 rounded-md bg-slate-50 border border-slate-200/70 p-1.5 flex flex-col justify-between overflow-hidden">
                {p.id === 'minimal' && (
                  <>
                    <div className="w-1/3 h-1 bg-slate-700 rounded-xs" />
                    <div className="space-y-1">
                      <div className="w-4/5 h-0.5 bg-slate-300 rounded-xs" />
                      <div className="w-2/3 h-0.5 bg-slate-200 rounded-xs" />
                    </div>
                  </>
                )}
                {p.id === 'corporate' && (
                  <>
                    <div>
                      <div className="w-2/5 h-1 bg-slate-800 rounded-xs" />
                      <div className="w-1/4 h-0.5 bg-[var(--color-proof)] mt-0.5" />
                    </div>
                    <div className="grid grid-cols-2 gap-1">
                      <div className="h-2 bg-slate-200/80 rounded-xs" />
                      <div className="h-2 bg-slate-200/80 rounded-xs" />
                    </div>
                  </>
                )}
                {p.id === 'bold' && (
                  <>
                    <div className="w-3/5 h-2 bg-slate-900 rounded-xs" />
                    <div className="w-full h-2.5 bg-slate-200 rounded-xs flex items-center px-1">
                      <div className="w-1/2 h-1 bg-[var(--color-proof)] rounded-xs" />
                    </div>
                  </>
                )}
                {p.id === 'data-dense' && (
                  <div className="space-y-0.5 w-full">
                    <div className="w-1/2 h-1 bg-slate-800" />
                    <div className="grid grid-cols-3 gap-0.5">
                      <div className="h-1.5 bg-slate-200" />
                      <div className="h-1.5 bg-slate-200" />
                      <div className="h-1.5 bg-slate-200" />
                    </div>
                    <div className="grid grid-cols-3 gap-0.5">
                      <div className="h-1.5 bg-slate-100" />
                      <div className="h-1.5 bg-slate-100" />
                      <div className="h-1.5 bg-slate-100" />
                    </div>
                  </div>
                )}
                {p.id === 'executive' && (
                  <div className="flex flex-col items-center justify-center h-full">
                    <div className="w-1/2 h-1 bg-slate-800 text-center" />
                    <div className="w-2/3 h-px bg-slate-300 mt-1" />
                  </div>
                )}
                {!['minimal', 'corporate', 'bold', 'data-dense', 'executive'].includes(p.id) && (
                  <div className="flex items-center justify-center h-full text-slate-400 font-mono text-[10px]">
                    {p.id}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-slate-900">{p.label}</span>
                {isSelected && (
                  <span className="w-2 h-2 rounded-full bg-[var(--color-proof)]" />
                )}
              </div>
            </div>

            <p className="text-[11px] text-slate-500 leading-normal line-clamp-2">
              {p.description}
            </p>
          </button>
        );
      })}
    </div>
  );
};
