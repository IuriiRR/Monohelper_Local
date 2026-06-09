/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// API paths proxied to the FastAPI backend during `vite dev`.
const API_PREFIXES = [
  '/accounts',
  '/transactions',
  '/reports',
  '/sync',
  '/tasks',
  '/users',
  '/openapi.json',
]

const BACKEND = 'http://127.0.0.1:8088'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // Production assets are served under a runtime-injected prefix (gateway: /cloudapi/app,
  // direct: /app). We build with a placeholder that src/web.py rewrites per request.
  // In dev, Vite serves at the root, so the base is '/'.
  base: mode === 'production' ? '/__APP_BASE__/' : '/',
  server: {
    proxy: Object.fromEntries(
      API_PREFIXES.map((p) => [p, { target: BACKEND, changeOrigin: true }]),
    ),
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
}))
