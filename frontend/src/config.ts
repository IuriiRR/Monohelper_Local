/**
 * Runtime base configuration for dual-mode deployment.
 *
 * `src/web.py` injects `window.__API_BASE__` and `window.__APP_BASE__` into the served
 * index.html based on the request's `X-Forwarded-Prefix`:
 *   - Gateway:  __API_BASE__ = "/cloudapi",  __APP_BASE__ = "/cloudapi/app"
 *   - Direct:   __API_BASE__ = "",            __APP_BASE__ = "/app"
 *   - Vite dev: neither injected -> both default to "" (API calls hit the dev proxy).
 *
 * NEVER hardcode "/cloudapi" anywhere in the frontend; always read from here.
 */
declare global {
  interface Window {
    __API_BASE__?: string
    __APP_BASE__?: string
    __API_KEY__?: string
  }
}

export const apiBase = window.__API_BASE__ ?? ''
export const routerBase = window.__APP_BASE__ ?? ''
export const apiKey = window.__API_KEY__ ?? import.meta.env.VITE_API_KEY ?? ''
