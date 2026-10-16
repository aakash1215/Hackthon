// Rebuild the phone profile (the shape onboarding saves) from the hub's worker/site/parties.
// Used by login (A1) and the demo persona loader.
import { createStore, keys } from 'idb-keyval'
import { remove, withLock } from './db.js'

const CAT_LABEL = { unskilled: 'helper', skilled: 'mistri', semi_skilled: 'carpenter' }

export function profileFromServer(res, extra = {}) {
  const w = res.worker || {}
  const s = res.site || {}
  const tk = (res.parties || []).filter((p) => ['contractor', 'mukadam', 'subcontractor'].includes(p.role)).pop() || {}
  return {
    language: w.language || 'hi', consent_keep_audio: !!w.consent_keep_audio, display_name: w.display_name || '',
    category_label: CAT_LABEL[w.category] || 'unknown', category: w.category || null, category_confirmed: !!w.category,
    site: { name: s.name || '', landmark: s.landmark || '', city: s.city || '', zone: s.zone || null,
      zone_confirmed: !!s.zone_confirmed, sphere: s.sphere || 'unknown' },
    gps: s.site_lat != null ? { lat: s.site_lat, lon: s.site_lon, acc: s.site_gps_accuracy_m } : null,
    gps_opt_in: !!w.gps_opt_in,
    thekedar: { name: tk.name || '', phone: tk.phone || '', phone_unknown: !tk.phone },
    usual: { start: '09:00', end: '19:00', break_min: w.default_break_min ?? 60 },
    agreed_daily: '', wage_period: s.wage_period || 'unknown',
    worker_id: w.id, onboarded: true, created: new Date().toISOString(), ...extra,
  }
}

/** Another person's local queue/records/caches must not show under this profile. */
export async function clearLocalData() {
  const store = createStore('apna-hisaab', 'kv')
  await withLock(async () => {
    for (const k of await keys(store)) {
      if (k === 'records' || k === 'jobs' || String(k).startsWith('cache:')) await remove(k)
    }
  })
}
