// Offline queue: every write (profile, recordings) is a job in IndexedDB, uploaded in order when the
// hub is reachable. Recordings are hashed on the phone first; the hub must report the same SHA-256.
import { apiForm, apiJson, ApiError, NetworkError } from './api.js'
import { getJobs, getRecords, patchJob, pushJob, shiftJob, updateRecord } from './db.js'
import { sha256Hex } from './hash.js'

const listeners = new Set()
let state = { online: navigator.onLine, hub: null, queued: 0, running: false }

export function subscribe(fn) {
  listeners.add(fn)
  fn(state)
  return () => listeners.delete(fn)
}
function emit(patch) {
  state = { ...state, ...patch }
  listeners.forEach((fn) => fn(state))
}
export const syncState = () => state

export async function refreshCounts() {
  const jobs = await getJobs()
  emit({ queued: jobs.filter((j) => j.type === 'entry').length, jobsTotal: jobs.length })
}

/** Save a recording: hash on the phone, store in IndexedDB, queue the upload. Never needs the network. */
export async function saveRecording({
  kind, workerId, audio, photo, gps, clientTs, durationS,
  speaker = 'worker', noticePlayed = false, noticeLang = null, consentRefused = false, extra = {},
}) {
  const localId = crypto.randomUUID()
  const sha = await sha256Hex(audio)
  const photoSha = photo ? await sha256Hex(photo) : null
  await updateRecord(localId, {
    kind, speaker, createdAt: clientTs, sha256: sha, photoSha256: photoSha, bytes: audio.size, durationS,
    gps: gps || null, status: 'queued', serverId: null, hashMatch: null, error: null, consentRefused, ...extra,
  })
  await pushJob({
    type: 'entry', localId, kind, workerId, audio, photo: photo || null, gps: gps || null, clientTs, sha,
    photoSha, speaker, noticePlayed, noticeLang, consentRefused,
  })
  await refreshCounts()
  flush()
  return { localId, sha256: sha }
}

/**
 * Save a standalone evidence photo (payment receipt, site board): hash on the phone, queue the upload.
 * Works offline; returns the phone-side SHA-256 for the save code shown to the worker.
 */
export async function savePhoto({ workerId, kind, photo, entryId = null, caption = '', gps = null, clientTs }) {
  const sha = await sha256Hex(photo)
  await pushJob({ type: 'photo', workerId, kind, photo, entryId, caption, gps, clientTs, sha })
  await refreshCounts()
  flush()
  return { sha256: sha }
}

export const queueJson = async (method, path, body) => {
  await pushJob({ type: 'json', method, path, body })
  await refreshCounts()
  flush()
}

async function runJob(job) {
  if (job.type === 'json') {
    await apiJson(job.method, job.path, job.body)
    return
  }
  if (job.type === 'entry') {
    const f = new FormData()
    const ext = (job.audio.type || '').includes('mp4') ? 'm4a' : 'webm'
    f.append('audio', job.audio, `note.${ext}`)
    f.append('kind', job.kind)
    f.append('worker_id', job.workerId)
    f.append('client_ts', job.clientTs)
    f.append('client_sha256', job.sha)
    if (job.speaker) f.append('speaker', job.speaker)
    if (job.noticePlayed) f.append('notice_played', 'true')
    if (job.noticeLang) f.append('notice_lang', job.noticeLang)
    if (job.consentRefused) f.append('consent_refused', 'true')
    if (job.photo) {
      f.append('photo', job.photo, 'photo.jpg')
      if (job.photoSha) f.append('photo_client_sha256', job.photoSha)
    }
    if (job.gps) {
      f.append('lat', String(job.gps.lat))
      f.append('lon', String(job.gps.lon))
      if (job.gps.acc != null) f.append('gps_accuracy_m', String(job.gps.acc))
      if (job.gps.ts) f.append('gps_ts', job.gps.ts)
    }
    const res = await apiForm('/api/entries', f, { timeoutMs: 120000 })
    await updateRecord(job.localId, {
      serverId: res.entry_id,
      serverSha256: res.audio_sha256,
      hashMatch: res.hash_match,
      status: res.hash_match === false ? 'hash_mismatch' : 'saved',
      gpsSaved: res.gps_saved,
    })
    return
  }
  if (job.type === 'photo') {
    const f = new FormData()
    f.append('photo', job.photo, 'photo.jpg')
    f.append('worker_id', job.workerId)
    f.append('kind', job.kind)
    if (job.entryId) f.append('entry_id', job.entryId)
    f.append('client_ts', job.clientTs)
    f.append('client_sha256', job.sha)
    if (job.caption) f.append('caption', job.caption)
    if (job.gps) {
      f.append('lat', String(job.gps.lat))
      f.append('lon', String(job.gps.lon))
      if (job.gps.acc != null) f.append('gps_accuracy_m', String(job.gps.acc))
    }
    await apiForm('/api/evidence/photo', f, { timeoutMs: 120000 })
  }
}

let flushing = null
/** Upload queued jobs in order. Network errors stop the loop (retry later); 4xx marks the job failed. */
export function flush() {
  if (flushing) return flushing
  flushing = (async () => {
    emit({ running: true })
    try {
      for (;;) {
        const jobs = await getJobs()
        const job = jobs.find((j) => !j.failed)
        if (!job) break
        try {
          await runJob(job)
          await shiftJob(job.id)
          emit({ hub: true })
        } catch (e) {
          if (e instanceof NetworkError || (e instanceof ApiError && e.status >= 500)) {
            emit({ hub: false })
            await patchJob(job.id, { attempts: (job.attempts || 0) + 1, lastError: e.message })
            break
          }
          // A 4xx will not succeed on retry; keep it visible instead of dropping it.
          await patchJob(job.id, { failed: true, lastError: e.code || e.message })
          if (job.localId) await updateRecord(job.localId, { status: 'failed', error: e.code || e.message })
        }
      }
    } finally {
      await refreshCounts()
      emit({ running: false })
      flushing = null
    }
  })()
  return flushing
}

let started = false
export function startSync() {
  if (started) return
  started = true
  window.addEventListener('online', () => { emit({ online: true }); flush() })
  window.addEventListener('offline', () => emit({ online: false, hub: false }))
  setInterval(() => { if (navigator.onLine) flush() }, 30000)
  refreshCounts()
  flush()
}

export async function pendingRecords() {
  const all = await getRecords()
  return Object.values(all)
    .filter((r) => r.status !== 'confirmed' && !r.consentRefused)
    .sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))
}
