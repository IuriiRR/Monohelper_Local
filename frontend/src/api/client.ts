/**
 * Typed API client. Types in `./schema.d.ts` are generated from FastAPI's OpenAPI schema
 * via `npm run gen-types` (see Makefile `gen-types`). Never hand-edit schema.d.ts.
 *
 * `baseUrl` comes from `apiBase` (runtime-injected prefix) so the same bundle works behind
 * the gateway (/cloudapi) and on direct access (no prefix). See src/config.ts.
 */
import createClient from 'openapi-fetch'
import type { paths } from './schema'
import { apiBase, apiKey } from '../config'

export const api = createClient<paths>({
  baseUrl: apiBase,
  headers: { 'X-API-Key': apiKey },
})
