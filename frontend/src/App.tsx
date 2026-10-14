import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { ConvertPage } from './pages/ConvertPage';
import { BrandsPage } from './pages/BrandsPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'convert' | 'brands'>('convert');

  return (
    <div className="min-h-screen bg-[var(--color-board)] text-[var(--color-ink)] flex flex-col font-sans selection:bg-[var(--color-proof-soft)] selection:text-[var(--color-proof)]">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="flex-1 pb-20">
        {activeTab === 'convert' ? <ConvertPage /> : <BrandsPage />}
      </main>
    </div>
  );
};

export default App;
