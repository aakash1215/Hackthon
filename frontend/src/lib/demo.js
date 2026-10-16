// Demo persona loader: https://<hub>/?demo=demo-sunita (P6, SYNTHETIC DEMO DATA).
// Only seeded demo ids ("demo-…") load this way; real workers log in with their PIN (A1).
// On any failure it does nothing.
import { apiJson } from './api.js'
import { getProfile, saveProfile } from './db.js'
import { clearLocalData, profileFromServer } from './profile.js'

export async function loadDemoFromUrl() {
  const params = new URLSearchParams(window.location.search)
  const id = params.get('demo')
  if (!id || !/^demo-[\w-]{1,34}$/.test(id)) return false
  // Never swap a real logged-in worker into the demo account: their next recordings and photos would be
  // saved under the demo id, and the demo's photos would show up in "their" evidence file.
  const current = await getProfile()
  if (current && !current.demo) {
    window.history.replaceState(null, '', window.location.pathname)
    return false
  }
  let res
  try {
    res = await apiJson('GET', `/api/workers/${encodeURIComponent(id)}`, null, { timeoutMs: 8000 })
  } catch {
    return false
  }
  await clearLocalData()
  await saveProfile(profileFromServer(res, { demo: true }))
  window.history.replaceState(null, '', window.location.pathname)
  return true
}
