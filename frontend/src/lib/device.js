// GPS (opt-in only) and read-aloud via the phone's own speech engine (no network, no AI model).

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

export function speak(text, lang = 'hi-IN') {
  if (!('speechSynthesis' in window) || !text) return false
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = lang
  const voice = window.speechSynthesis.getVoices().find((v) => v.lang && v.lang.toLowerCase().startsWith(lang.slice(0, 2)))
  if (voice) u.voice = voice
  u.rate = 0.95
  window.speechSynthesis.speak(u)
  return true
}

function voiceFor(lang) {
  const voices = window.speechSynthesis.getVoices()
  return voices.find((v) => v.lang && v.lang.toLowerCase().replace('_', '-') === lang.toLowerCase())
    || voices.find((v) => v.lang && v.lang.toLowerCase().startsWith(lang.slice(0, 2)))
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
  if (!('speechSynthesis' in window) || !text) return false
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
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}
