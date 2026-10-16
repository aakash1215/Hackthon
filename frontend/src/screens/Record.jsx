// Record (UI/ D2) → optional photo + GPS step (composed in the same style; BUILD_PLAN P2) → save.
// The audio is hashed and stored on the phone before anything is uploaded.
import { useEffect, useRef, useState } from 'react'
import { Banknote, Camera, Check, Clock, Coffee, HardHat, Lock, MapPin, Users, Wallet, CalendarDays } from 'lucide-react'
import { Btn, TopBar, useApp } from '../components/Ui.jsx'
import { getFix } from '../lib/device.js'
import { localIso, dayMonth, todayIso } from '../lib/format.js'
import { startRecorder } from '../lib/recorder.js'
import { saveRecording } from '../lib/sync.js'

const MAX_MS = 60000
const BARS = 30
// Bar-height pattern traced from UI/ D2; the live mic level scales it.
const SHAPE = [0.35, 0.6, 0.75, 0.6, 1, 0.8, 0.45, 0.7, 0.55, 0.6, 0.95, 0.85, 0.5, 0.8, 0.65, 0.4, 0.7, 0.9, 0.55, 0.45, 0.75, 0.6, 0.4, 0.85, 1, 0.6, 0.5, 0.9, 0.7, 0.55]
const PROMPTS = {
  workday: [[Clock, 'कब से कब तक'], [HardHat, 'ठेकेदार'], [Users, 'साथ में कौन'], [Coffee, 'आराम कितना']],
  payment: [[Banknote, 'कितना मिला'], [HardHat, 'किसने दिया'], [Wallet, 'नकद या UPI'], [CalendarDays, 'किस काम का']],
}

export default function Record({ kind = 'workday' }) {
  const { profile, back, replace, toast } = useApp()
  const [phase, setPhase] = useState('starting') // starting | recording | photo | saving | error
  const [elapsed, setElapsed] = useState(0)
  const [levels, setLevels] = useState(() => Array(BARS).fill(0.08))
  const [audio, setAudio] = useState(null)
  const [photo, setPhoto] = useState(null)
  const [photoUrl, setPhotoUrl] = useState(null)
  const [gps, setGps] = useState(null)
  const [gpsState, setGpsState] = useState('idle')
  const recRef = useRef(null)
  const levelRef = useRef(0)
  const fileRef = useRef(null)
  const clientTs = useRef(localIso())

  useEffect(() => {
    let cancelled = false
    startRecorder({
      maxMs: MAX_MS,
      onLevel: (v) => { levelRef.current = v },
      onAutoStop: () => toast('60 सेकंड पूरे — रिकॉर्डिंग रुक गई'),
    }).then((rec) => {
      if (cancelled) { rec.cancel(); return }
      recRef.current = rec
      setPhase('recording')
    }).catch(() => setPhase('error'))
    return () => { cancelled = true; recRef.current?.cancel() }
  }, [toast])

  useEffect(() => {
    if (phase !== 'recording') return
    const t = setInterval(() => {
      const ms = Date.now() - recRef.current.started
      setElapsed(ms)
      setLevels((l) => [...l.slice(1), Math.max(0.08, levelRef.current)])
      if (ms >= MAX_MS) stop()
    }, 120)
    return () => clearInterval(t)
  }, [phase])

  async function stop() {
    if (!recRef.current) return
    const rec = recRef.current
    recRef.current = null
    const out = await rec.stop()
    setAudio(out)
    setPhase('photo')
    if (profile.gps_opt_in) {
      setGpsState('locating')
      const fix = await getFix({ timeoutMs: 8000 })
      setGps(fix)
      setGpsState(fix ? 'ok' : 'none')
    }
  }

  function cancel() {
    recRef.current?.cancel()
    back()
  }

  function onPhoto(e) {
    const f = e.target.files?.[0]
    if (!f) return
    setPhoto(f)
    setPhotoUrl(URL.createObjectURL(f))
  }

  async function save() {
    setPhase('saving')
    try {
      const r = await saveRecording({
        kind, workerId: profile.worker_id, audio: audio.blob, photo, gps: profile.gps_opt_in ? gps : null,
        clientTs: clientTs.current, durationS: audio.durationS,
      })
      replace('saved', { localId: r.localId })
    } catch {
      setPhase('photo')
      toast('फ़ोन में सेव नहीं हो पाया — फिर कोशिश करें')
    }
  }

  const secs = Math.floor(elapsed / 1000)
  const mmss = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`
  const playedBars = Math.round((elapsed / MAX_MS) * BARS)

  if (phase === 'error') {
    return (
      <div className="screen">
        <TopBar onCancel={back} speakText="माइक नहीं मिला। फ़ोन की सेटिंग में माइक की इजाज़त दें।" />
        <h1 className="title">माइक नहीं मिला</h1>
        <p className="subtitle">फ़ोन की सेटिंग में इस ऐप को माइक की इजाज़त दें, फिर दोबारा कोशिश करें।</p>
        <div className="bottom-actions"><Btn onClick={back}>ठीक है</Btn></div>
      </div>
    )
  }

  if (phase === 'photo' || phase === 'saving') {
    return (
      <div className="screen">
        <TopBar onCancel={cancel} speakText="आवाज़ रिकॉर्ड हो गई। चाहें तो फ़ोटो जोड़ें, फिर सेव करें।" />
        <h1 className="title">फ़ोटो जोड़ें?</h1>
        <p className="subtitle">{kind === 'payment' ? 'रसीद या UPI मैसेज की फ़ोटो — चाहें तो' : 'साइट या काम की फ़ोटो — चाहें तो'}</p>
        <div className="card pad stack">
          <div className="row">
            <span className="icon-bubble cream"><Check size={18} /></span>
            <div className="grow"><b>आवाज़ रिकॉर्ड हुई</b><div className="small" style={{ color: 'var(--text-2)' }}>{audio?.durationS || 0} सेकंड · {dayMonth(todayIso())}</div></div>
          </div>
          {photoUrl && <img className="photo-thumb" src={photoUrl} alt="जोड़ी गई फ़ोटो" />}
          <input ref={fileRef} className="hidden-input" type="file" accept="image/*" capture="environment" onChange={onPhoto} />
          <Btn variant="outline" icon={Camera} onClick={() => fileRef.current?.click()}>{photo ? 'दूसरी फ़ोटो लें' : 'फ़ोटो लें'}</Btn>
        </div>
        {profile.gps_opt_in && (
          <div style={{ marginTop: 12 }}>
            {gpsState === 'locating' && <span className="gps-chip"><MapPin size={16} /> जगह ढूँढ रहे हैं…</span>}
            {gpsState === 'ok' && gps && <span className="gps-chip"><MapPin size={16} /> {gps.lat.toFixed(5)}, {gps.lon.toFixed(5)} · ±{gps.acc} मी</span>}
            {gpsState === 'none' && <span className="gps-chip" style={{ color: 'var(--text-2)' }}><MapPin size={16} /> जगह नहीं मिली — बिना GPS सेव होगा</span>}
          </div>
        )}
        <div className="lock-note"><Lock size={16} /> पहले इसी फ़ोन में सेव होगा, फिर हब पर</div>
        <div className="bottom-actions" style={{ marginTop: 12 }}>
          <Btn icon={Check} onClick={save} disabled={phase === 'saving'}>{phase === 'saving' ? 'सेव हो रहा है…' : 'सेव करें'}</Btn>
        </div>
      </div>
    )
  }

  return (
    <div className="screen">
      <TopBar onCancel={cancel} speakText="बोलिए, सुन रहे हैं। कब से कब तक काम किया, ठेकेदार कौन, साथ में कौन, आराम कितना।" />
      <div className="rec-title"><span className="rec-dot" /> बोलिए… सुन रहे हैं</div>
      <div className="center muted">आज, {dayMonth(todayIso())}</div>
      <div className="timer">{phase === 'starting' ? '0:00' : mmss}</div>
      <div className="center small">60 सेकंड तक बोल सकते हैं</div>
      <div className="wave" aria-hidden>
        {levels.map((v, i) => <i key={i} className={i < playedBars ? 'on' : ''} style={{ height: `${Math.round(8 + SHAPE[i] * (16 + Math.min(1, v * 1.6) * 30))}px` }} />)}
      </div>
      <div className="label">ये बताएँ:</div>
      <div className="prompt-chips">
        {PROMPTS[kind].map(([I, t]) => <span key={t}><I size={18} /> {t}</span>)}
      </div>
      <div className="stop-wrap">
        <button className="stop-btn" onClick={stop} disabled={phase !== 'recording'} aria-label="रोकें">
          <span><b /></span>
        </button>
        <div className="stop-label">रोकें</div>
      </div>
      <div className="lock-note"><Lock size={16} /> आवाज़ सीधे इसी फ़ोन में सेव होती है</div>
    </div>
  )
}
