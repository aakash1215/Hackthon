// Microphone recording with MediaRecorder. Returns the original bytes as a Blob; nothing is transcoded
// on the phone, so the hash covers exactly what was recorded.
const MIME = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus']

export async function startRecorder({ maxMs = 60000, onLevel, onAutoStop } = {}) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
  const mimeType = MIME.find((m) => window.MediaRecorder && MediaRecorder.isTypeSupported?.(m)) || ''
  const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
  const chunks = []
  rec.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data) }

  let ctx = null
  let raf = 0
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)()
    const src = ctx.createMediaStreamSource(stream)
    const an = ctx.createAnalyser()
    an.fftSize = 512
    src.connect(an)
    const buf = new Uint8Array(an.fftSize)
    const tick = () => {
      an.getByteTimeDomainData(buf)
      let sum = 0
      for (const v of buf) sum += ((v - 128) / 128) ** 2
      onLevel?.(Math.min(1, Math.sqrt(sum / buf.length) * 4))
      raf = requestAnimationFrame(tick)
    }
    tick()
  } catch {
    // Level meter is cosmetic; recording works without it.
  }

  const started = Date.now()
  rec.start(1000)

  let finish
  const done = new Promise((resolve) => { finish = resolve })
  rec.onstop = () => {
    cancelAnimationFrame(raf)
    ctx?.close().catch(() => {})
    stream.getTracks().forEach((t) => t.stop())
    finish({ blob: new Blob(chunks, { type: rec.mimeType || mimeType || 'audio/webm' }), durationS: Math.round((Date.now() - started) / 1000) })
  }
  const timer = setTimeout(() => { if (rec.state !== 'inactive') { rec.stop(); onAutoStop?.() } }, maxMs)

  return {
    started,
    stop() {
      clearTimeout(timer)
      if (rec.state !== 'inactive') rec.stop()
      return done
    },
    cancel() {
      clearTimeout(timer)
      if (rec.state !== 'inactive') rec.stop()
    },
  }
}
