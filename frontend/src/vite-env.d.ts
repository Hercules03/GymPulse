/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_CHAT_API_URL: string;
  readonly VITE_WEBSOCKET_URL: string;
  readonly VITE_ENABLE_WEBSOCKET: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}