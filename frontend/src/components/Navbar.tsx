import React from 'react';
import { Layers, ShieldCheck, Sparkles, Terminal } from 'lucide-react';

interface NavbarProps {
  activeTab: 'convert' | 'brands';
  setActiveTab: (tab: 'convert' | 'brands') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="h-16 border-b border-[var(--color-rule)] bg-white/95 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
      {/* Brand & Identity */}
      <div className="flex items-center gap-3.5">
        <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white shadow-xs">
          <Terminal className="w-4 h-4 text-rose-400" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-display font-bold text-slate-900 text-lg tracking-tight">
              htmlppt
            </span>
            <span className="font-mono text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
              v1.0 proof studio
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200" aria-label="Main Navigation">
        <button
          type="button"
          onClick={() => setActiveTab('convert')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'convert'
              ? 'bg-white text-slate-900 shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-[var(--color-proof)]" />
          Converter Studio
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('brands')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'brands'
              ? 'bg-white text-slate-900 shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
          Brand Profiles & Templates
        </button>
      </nav>

      {/* Right meta tag */}
      <div className="hidden md:flex items-center gap-2 text-xs text-slate-500">
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-600">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          <span>Native OpenXML (.pptx)</span>
        </div>
      </div>
    </header>
  );
};
