// GPS (opt-in only) and read-aloud via the phone's own speech engine (no network, no AI model),
// or the optional ChatGPT voice when the worker picked the cloud engine.
import { getEngine } from './engine.js'

export function getFix({ timeoutMs = 10000 } = {}) {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({
        lat: Number(p.coords.latitude.toFixed(6)),
        lon: Number(p.coords.longitude.toFixed(6)),
        acc: Math.round(p.coords.accuracy),
        ts: new Date(p.timestamp).toISOString(),
      }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 30000 },
    )
  })
}

// --- optional ChatGPT voice (female), only when the worker picked the cloud engine in Settings -------
// Fetches an MP3 of the same on-screen text from the hub (/api/tts). Any failure → the phone's own voice.
let cloudAudio = null // { el, finish }
let cloudSeq = 0

function stopCloud() {
  cloudSeq += 1
  if (cloudAudio) { cloudAudio.el.pause(); cloudAudio.finish('stopped') }
}

/** Resolves 'ok' (played to the end) | 'fail' (fall back to the phone's voice) | 'stopped'. */
async function speakCloud(text, lang) {
  stopCloud()
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
  const my = cloudSeq
  let url = null
  const ctrl = new AbortController()
  const t = setTimeout(() => ctrl.abort(), 12000)
  try {
    const res = await fetch('/api/tts', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang: lang.slice(0, 2) }), signal: ctrl.signal,
    })
    if (res.ok) url = URL.createObjectURL(await res.blob())
  } catch {
    url = null
  } finally {
    clearTimeout(t)
  }
  if (my !== cloudSeq) { if (url) URL.revokeObjectURL(url); return 'stopped' }
  if (!url) return 'fail'
  return new Promise((resolve) => {
    const el = new Audio(url)
    let settled = false
    const finish = (r) => {
      if (settled) return
      settled = true
      URL.revokeObjectURL(url)
      if (cloudAudio?.el === el) cloudAudio = null
      resolve(r)
    }
    cloudAudio = { el, finish }
    el.onended = () => finish('ok')
    el.onerror = () => finish('fail')
    el.play().catch(() => finish('fail'))
  })
}

export function speak(text, lang = 'hi-IN') {
  if (!text) return false
  if (getEngine() === 'cloud') {
    speakCloud(text, lang).then((r) => { if (r === 'fail') speakLocal(text, lang) })
    return true
  }
  return speakLocal(text, lang)
}

function speakLocal(text, lang) {
  if (!('speechSynthesis' in window) || !text) return false
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = lang
  const voice = voiceFor(lang)
  if (voice) u.voice = voice
  u.rate = 0.95
  window.speechSynthesis.speak(u)
  return true
}

// "सुनें" uses a female voice where the phone offers one. Browsers don't expose gender,
// so match known voice names (Google, Microsoft, Apple, Android Google TTS codes).
const FEMALE = /female|swara|kalpana|lekha|heera|aarohi|ananya|aarti|google हिन्दी|google मराठी|hi-in-x-hia|hi-in-x-hic|mr-in-x-mra/i
const MALE = /male|hemant|madhur|rishi|ravi|prabhat|aarav|manohar|hi-in-x-hid|hi-in-x-hie|mr-in-x-mrb/i

function voiceFor(lang) {
  const all = window.speechSynthesis.getVoices()
  const exact = all.filter((v) => v.lang && v.lang.toLowerCase().replace('_', '-') === lang.toLowerCase())
  const voices = exact.length ? exact : all.filter((v) => v.lang && v.lang.toLowerCase().startsWith(lang.slice(0, 2)))
  const tag = (v) => `${v.name} ${v.voiceURI}`
  return voices.find((v) => FEMALE.test(tag(v)))
    || voices.find((v) => !MALE.test(tag(v)))
    || voices[0]
}

// Voices load asynchronously on Android Chrome; wait briefly for them.
function voicesReady(ms = 1200) {
  return new Promise((resolve) => {
    if (window.speechSynthesis.getVoices().length) return resolve()
    const t = setTimeout(resolve, ms)
    window.speechSynthesis.addEventListener?.('voiceschanged', () => { clearTimeout(t); resolve() }, { once: true })
  })
}

/**
 * Speak and resolve when finished: true = the phone's own voice spoke it to the end,
 * false = no voice for this language or speech was interrupted (callers then show the text + a countdown).
 */
export async function speakAsync(text, lang = 'hi-IN') {
  if (!text) return false
  if (getEngine() === 'cloud') {
    const r = await speakCloud(text, lang)
    if (r !== 'fail') return r === 'ok'
  }
  if (!('speechSynthesis' in window)) return false
  await voicesReady()
  const voice = voiceFor(lang)
  if (!voice) return false
  window.speechSynthesis.cancel()
  return new Promise((resolve) => {
    const u = new SpeechSynthesisUtterance(text)
    u.lang = lang
    u.voice = voice
    u.rate = 0.95
    let settled = false
    const done = (ok) => { if (!settled) { settled = true; clearTimeout(guard); resolve(ok) } }
    // Some Android engines never fire onend; assume finished after a generous estimate.
    const guard = setTimeout(() => done(true), 3000 + text.length * 110)
    u.onend = () => done(true)
    u.onerror = () => done(false)
    window.speechSynthesis.speak(u)
  })
}

export function stopSpeaking() {
  stopCloud()
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}
