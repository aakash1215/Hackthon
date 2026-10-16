// Mic button inside a .field: tap to speak, tap again to stop. The hub's local Whisper transcribes it
// (POST /api/dictate, no LLM); the text only pre-fills the input, and the worker can still edit it.
import { useEffect, useRef, useState } from 'react'
import { Mic, Square } from 'lucide-react'
import { Spinner, useApp } from './Ui.jsx'
import * as api from '../lib/api.js'
import { startRecorder } from '../lib/recorder.js'
import { getEngine } from '../lib/engine.js'

const MAX_MS = 8000

export default function VoiceInput({ onText, field = 'text', language = 'hi', keepAudio = true, label = 'बोलकर भरें' }) {
  const { toast } = useApp()
  const [state, setState] = useState('idle') // idle | rec | busy
  const rec = useRef(null)

  useEffect(() => () => rec.current?.cancel(), [])

  async function send(blob) {
    setState('busy')
    try {
      const form = new FormData()
      form.append('audio', blob, `clip.${blob.type.includes('mp4') ? 'm4a' : blob.type.includes('ogg') ? 'ogg' : 'webm'}`)
      form.append('language', language)
      form.append('field', field)
      form.append('keep_audio', String(keepAudio))
      form.append('engine', getEngine())
      const res = await api.apiForm('/api/dictate', form, { timeoutMs: 120000 })
      if (res.text) onText(res.text)
      else toast('आवाज़ साफ़ नहीं आई — फिर से बोलें')
    } catch (e) {
      if (e instanceof api.NetworkError) toast('हब से नहीं जुड़ पाए — लिखकर भरें')
      else if (e.code === 'ASR_UNAVAILABLE') toast('आवाज़ से भरना अभी बंद है — लिखकर भरें')
      else toast('नहीं हो पाया — लिखकर भरें')
    } finally {
      setState('idle')
    }
  }

  async function tap() {
    if (state === 'busy') return
    if (state === 'rec') {
      const r = rec.current
      rec.current = null
      const { blob } = await r.stop()
      send(blob)
      return
    }
    try {
      rec.current = await startRecorder({
        maxMs: MAX_MS,
        onAutoStop: async () => {
          const r = rec.current
          rec.current = null
          if (r) send((await r.stop()).blob)
        },
      })
      setState('rec')
    } catch {
      toast('माइक नहीं खुला — फ़ोन में माइक की इजाज़त दें')
    }
  }

  return (
    <button type="button" className={`mic-btn ${state}`} onClick={tap} disabled={state === 'busy'}
      aria-label={state === 'rec' ? 'रोकें' : label}>
      {state === 'busy' ? <Spinner /> : state === 'rec' ? <Square size={18} fill="currentColor" /> : <Mic size={22} />}
    </button>
  )
}
