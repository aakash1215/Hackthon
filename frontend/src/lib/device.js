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
