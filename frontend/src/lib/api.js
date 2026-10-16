// Thin client for the hub API (same origin). Errors carry the server's code, never a guess.
export class ApiError extends Error {
  constructor(status, code) {
    super(code)
    this.status = status
    this.code = code
  }
}

export class NetworkError extends Error {}

async function handle(res) {
  let body = null
  try {
    body = await res.json()
  } catch {
    body = null
  }
  if (!res.ok) throw new ApiError(res.status, (body && (body.detail || body.error)) || `HTTP_${res.status}`)
  return body
}

export async function apiJson(method, path, body, { timeoutMs = 20000 } = {}) {
  const ctrl = new AbortController()
  const t = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const res = await fetch(path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    })
    return await handle(res)
  } catch (e) {
    if (e instanceof ApiError) throw e
    throw new NetworkError(String(e))
  } finally {
    clearTimeout(t)
  }
}

export async function apiForm(path, form, { timeoutMs = 60000 } = {}) {
  const ctrl = new AbortController()
  const t = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const res = await fetch(path, { method: 'POST', body: form, signal: ctrl.signal })
    return await handle(res)
  } catch (e) {
    if (e instanceof ApiError) throw e
    throw new NetworkError(String(e))
  } finally {
    clearTimeout(t)
  }
}

export const getEntry = (id) => apiJson('GET', `/api/entries/${id}`)
// Processing runs ASR + the LLM on the hub; on the CPU tier this can take 1–2 minutes.
export const processEntry = (id) => apiJson('POST', `/api/entries/${id}/process`, null, { timeoutMs: 300000 })
export const confirmEntry = (id, fields) => apiJson('POST', `/api/entries/${id}/confirm`, { fields })
export const ledger = (workerId, from, to) =>
  apiJson('GET', `/api/ledger?worker_id=${encodeURIComponent(workerId)}${from ? `&date_from=${from}` : ''}${to ? `&date_to=${to}` : ''}`)
export const hisaab = (workerId, from, to) =>
  apiJson('GET', `/api/hisaab?worker_id=${encodeURIComponent(workerId)}${from ? `&date_from=${from}` : ''}${to ? `&date_to=${to}` : ''}`)
export const chainVerify = () => apiJson('GET', '/api/chain/verify')
export const health = () => apiJson('GET', '/api/health', null, { timeoutMs: 4000 })
export function copyYesterday(workerId, clientTs) {
  const f = new FormData()
  f.append('worker_id', workerId)
  f.append('client_ts', clientTs)
  return apiForm('/api/entries/copy-yesterday', f)
}
