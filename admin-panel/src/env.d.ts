/// <reference types="vite/client" />

declare interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_WS_URL?: string;
  readonly VITE_DEFAULT_TZ?: 'Asia/Kuala_Lumpur' | 'UTC';
  readonly VITE_AUTH_STORAGE?: 'local' | 'session';
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv;
}
