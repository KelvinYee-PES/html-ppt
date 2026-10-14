/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional absolute API origin; defaults to same-origin (`/api` via Vite proxy). */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
