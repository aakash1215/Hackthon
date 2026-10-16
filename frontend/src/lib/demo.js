// Demo persona loader: https://<hub>/?demo=<worker_id> (P6, SYNTHETIC DEMO DATA).
// Fetches the seeded worker from the hub, rebuilds the profile in the shape onboarding saves,
// clears local records/jobs/caches and drops the query string. On any failure it does nothing.
import { createStore, keys } from 'idb-keyval'
import { apiJson } from './api.js'
import { remove, saveProfile, withLock } from './db.js'

const CAT_LABEL = { unskilled: 'helper', skilled: 'mistri', semi_skilled: 'carpenter' }

export async function loadDemoFromUrl() {
  const params = new URLSearchParams(window.location.search)
  const id = params.get('demo')
  if (!id || !/^[\w-]{1,40}$/.test(id)) return false
  let res
  try {
    res = await apiJson('GET', `/api/workers/${encodeURIComponent(id)}`, null, { timeoutMs: 8000 })
  } catch {
    return false
  }
  const w = res.worker || {}
  const s = res.site || {}
  const tk = (res.parties || []).filter((p) => ['contractor', 'mukadam', 'subcontractor'].includes(p.role)).pop() || {}
  const profile = {
    language: w.language || 'hi', consent_keep_audio: !!w.consent_keep_audio, display_name: w.display_name || '',
    category_label: CAT_LABEL[w.category] || 'unknown', category: w.category || null, category_confirmed: !!w.category,
    site: { name: s.name || '', landmark: s.landmark || '', city: s.city || '', zone: s.zone || null,
      zone_confirmed: !!s.zone_confirmed, sphere: s.sphere || 'unknown' },
    gps: s.site_lat != null ? { lat: s.site_lat, lon: s.site_lon, acc: s.site_gps_accuracy_m } : null,
    gps_opt_in: !!w.gps_opt_in,
    thekedar: { name: tk.name || '', phone: tk.phone || '', phone_unknown: !tk.phone },
    usual: { start: '09:00', end: '19:00', break_min: w.default_break_min ?? 60 },
    agreed_daily: '', wage_period: s.wage_period || 'unknown',
    worker_id: w.id, onboarded: true, created: new Date().toISOString(), demo: true,
  }
  const store = createStore('apna-hisaab', 'kv')
  await withLock(async () => {
    const all = await keys(store)
    for (const k of all) {
      if (k === 'records' || k === 'jobs' || String(k).startsWith('cache:')) await remove(k)
    }
  })
  await saveProfile(profile)
  window.history.replaceState(null, '', window.location.pathname)
  return true
}
