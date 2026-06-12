/**
 * Typed API client. Types in `./schema.d.ts` are generated from FastAPI's OpenAPI schema
 * via `npm run gen-types` (see Makefile `gen-types`). Never hand-edit schema.d.ts.
 *
 * `baseUrl` comes from `apiBase` (runtime-injected prefix) so the same bundle works behind
 * the gateway (/cloudapi) and on direct access (no prefix). See src/config.ts.
 *
 * The auth middleware reads the API key dynamically on every request (localStorage first,
 * then window.__API_KEY__, then VITE_API_KEY). On 401/403 it dispatches `api:unauthorized`
 * so the app can redirect to /setup.
 */
import createClient, { type Middleware } from 'openapi-fetch'
import type { paths } from './schema'
import { apiBase, getApiKey } from '../config'

const authMiddleware: Middleware = {
  onRequest({ request }) {
    const key = getApiKey()
    if (key) request.headers.set('X-API-Key', key)
    return request
  },
  onResponse({ response }) {
    if (response.status === 401 || response.status === 403) {
      window.dispatchEvent(new CustomEvent('api:unauthorized'))
    }
    return response
  },
}

export const api = createClient<paths>({ baseUrl: apiBase })
api.use(authMiddleware)
