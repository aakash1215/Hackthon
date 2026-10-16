// IndexedDB (idb-keyval) store for the profile, the offline job queue and local records.
// Writes go through a promise-chain lock so the sync loop and the UI never overwrite each other.
import { clear, createStore, del, get, set } from 'idb-keyval'

const store = createStore('apna-hisaab', 'kv')
let chain = Promise.resolve()

export function withLock(fn) {
  const run = chain.then(fn, fn)
  chain = run.catch(() => {})
  return run
}

export const read = async (key, fallback = null) => {
  const v = await get(key, store)
  return v === undefined ? fallback : v
}
export const write = (key, value) => set(key, value, store)
export const remove = (key) => del(key, store)
/** Log out: forget everything on this phone (profile, queue, records, caches). The hub keeps the record. */
export const clearPhone = () => withLock(() => clear(store))

// --- profile -----------------------------------------------------------------
export const getProfile = () => read('profile', null)
export const saveProfile = (p) => withLock(() => write('profile', p))

// --- records: one per recording, keyed by localId ------------------------------
export const getRecords = () => read('records', {})
export function updateRecord(localId, patch) {
  return withLock(async () => {
    const all = await read('records', {})
    all[localId] = { ...(all[localId] || { localId }), ...patch }
    await write('records', all)
    return all[localId]
  })
}
export function deleteRecord(localId) {
  return withLock(async () => {
    const all = await read('records', {})
    delete all[localId]
    await write('records', all)
  })
}

// --- jobs: ordered queue run by sync.js ------------------------------------------
export const getJobs = () => read('jobs', [])
export function pushJob(job) {
  return withLock(async () => {
    const jobs = await read('jobs', [])
    jobs.push({ id: crypto.randomUUID(), created: Date.now(), attempts: 0, ...job })
    await write('jobs', jobs)
  })
}
export function shiftJob(id) {
  return withLock(async () => {
    const jobs = await read('jobs', [])
    await write('jobs', jobs.filter((j) => j.id !== id))
  })
}
export function patchJob(id, patch) {
  return withLock(async () => {
    const jobs = await read('jobs', [])
    await write('jobs', jobs.map((j) => (j.id === id ? { ...j, ...patch } : j)))
  })
}
