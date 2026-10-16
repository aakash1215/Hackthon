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
// Processing runs ASR + the LLM on the hub (1–2 minutes on the CPU tier). The hub does it in the background,
// one note at a time; the phone only asks every few seconds, so a slow model, a proxy timeout or a sleeping
// phone never loses the work and retries never start a second model run.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
export async function processEntry(id, { onWait, maxMs = 20 * 60000 } = {}) {
  await apiJson('POST', `/api/entries/${id}/process?async=1`, null, { timeoutMs: 20000 })
  const t0 = Date.now()
  let netFails = 0
  for (;;) {
    let e
    try {
      e = await apiJson('GET', `/api/entries/${id}`, null, { timeoutMs: 15000 })
      netFails = 0
    } catch (err) {
      if (!(err instanceof NetworkError) || ++netFails >= 5) throw err
      await sleep(4000)
      continue
    }
    if (!e.processing) {
      return {
        entry_id: id, status: e.status, transcript: e.transcript, fields: e.reconciled?.fields || null,
        summary: e.reconciled?.summary || null, error: e.status === 'saved' ? (e.error || 'NOT_PROCESSED') : null,
        reply: e.reply || null, tier: 'server',
      }
    }
    onWait?.(e.queue_position)
    if (Date.now() - t0 > maxMs) throw new ApiError(504, 'PROCESSING_TIMEOUT')
    await sleep(3000)
  }
}
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

// --- P3: hisaab check, differences, evidence, coach, export -------------------------------------
const q = (workerId) => `worker_id=${encodeURIComponent(workerId)}`
export const manualStatement = (workerId, clientTs) =>
  apiJson('POST', '/api/entries/manual', { worker_id: workerId, kind: 'hisaab_statement', client_ts: clientTs })
export const differences = (id) => apiJson('GET', `/api/entries/${id}/differences`)
export const statements = (workerId) => apiJson('GET', `/api/statements?${q(workerId)}`)
export const evidenceList = (workerId, kind) => apiJson('GET', `/api/evidence?${q(workerId)}${kind ? `&kind=${kind}` : ''}`)
export const coach = (workerId) => apiJson('GET', `/api/coach?${q(workerId)}`)
// The packet build renders a PDF on the hub; allow it time.
export const exportPacket = (body) => apiJson('POST', '/api/export', body, { timeoutMs: 120000 })

// --- P4: Telegram thekedar agent, inbox, promises -------------------------------------------------
// The phone only triggers server-side templates; it never writes free text to the thekedar.
export const telegramStatus = (workerId) => apiJson('GET', `/api/telegram/status?${q(workerId)}`, null, { timeoutMs: 8000 })
export const telegramInvite = (workerId) => apiJson('POST', '/api/telegram/invite', { worker_id: workerId })
export const telegramSettings = (workerId, patch) => apiJson('POST', '/api/telegram/settings', { worker_id: workerId, ...patch })
export const agentAsk = (body) => apiJson('POST', '/api/agent/ask', body, { timeoutMs: 60000 })
export const telegramSend = (workerId, template) => apiJson('POST', '/api/telegram/send', { worker_id: workerId, template })
export const telegramMessages = (workerId) => apiJson('GET', `/api/telegram/messages?${q(workerId)}`, null, { timeoutMs: 8000 })
export const inbox = (workerId) => apiJson('GET', `/api/inbox?${q(workerId)}`, null, { timeoutMs: 8000 })
export const inboxAction = (id, body) => apiJson('POST', `/api/inbox/${encodeURIComponent(id)}`, body)
export const promises = (workerId) => apiJson('GET', `/api/promises?${q(workerId)}`)
