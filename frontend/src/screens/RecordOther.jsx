// Recording someone other than the worker (BUILD_PLAN §8 thekedar, §9 co-worker). Hard rule 5:
// it always starts with a notice that cannot be skipped, and Stop is instant.
//  - thekedar: pick notice language → the recorder starts and the phone speaks the notice (so it is on
//    the tape) → only then the Stop UI appears (UI/ S6 layout).
//  - coworker: pick the days → the consent prompt is spoken → "साथी राज़ी हैं" starts the recording.
import { useEffect, useRef, useState } from 'react'
import { Check, CircleCheck, Lock, Megaphone, Mic, Quote, Volume2 } from 'lucide-react'
import { Btn, Spinner, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { read } from '../lib/db.js'
import { getFix, speakAsync, stopSpeaking } from '../lib/device.js'
import { dayMonth, localIso, monthRange, shortDayDate, todayIso } from '../lib/format.js'
import { startRecorder } from '../lib/recorder.js'
import { saveRecording } from '../lib/sync.js'

const NOTICE = {
  hi: { label: 'हिंदी', lang: 'hi-IN', text: 'यह बातचीत रिकॉर्ड की जा रही है, ताकि हिसाब साफ़ रहे।' },
  mr: { label: 'मराठी', lang: 'mr-IN', text: 'हिशोब स्पष्ट राहावा म्हणून हे संभाषण रेकॉर्ड केलं जात आहे.' },
  en: { label: 'English', lang: 'en-IN', text: 'This conversation is being recorded so the account stays clear.' },
}
const MAX_MS = 60000
const FALLBACK_S = 6 // no TTS voice: show the text big and count down instead
const BARS = 30
const SHAPE = [0.35, 0.6, 0.75, 0.6, 1, 0.8, 0.45, 0.7, 0.55, 0.6, 0.95, 0.85, 0.5, 0.8, 0.65, 0.4, 0.7, 0.9, 0.55, 0.45, 0.75, 0.6, 0.4, 0.85, 1, 0.6, 0.5, 0.9, 0.7, 0.55]
const mmss = (ms) => { const s = Math.floor(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}` }

export default function RecordOther({ who = 'thekedar', dates: initialDates }) {
  const { profile, back, replace, toast } = useApp()
  const isTk = who === 'thekedar'
  const [phase, setPhase] = useState(isTk ? 'lang' : 'days') // lang | days | prompt | notice | recording | saving | savefail | error
  const [lang, setLang] = useState(NOTICE[profile.language] ? profile.language : 'hi')
  const [countdown, setCountdown] = useState(null)
  const [promptState, setPromptState] = useState('idle') // idle | playing | done
  const [elapsed, setElapsed] = useState(0)
  const [levels, setLevels] = useState(() => Array(BARS).fill(0.08))
  const [days, setDays] = useState(null)
  const [picked, setPicked] = useState(() => new Set(initialDates || []))
  const recRef = useRef(null)
  const outRef = useRef(null)
  const levelRef = useRef(0)
  const gpsRef = useRef(null)
  const alive = useRef(true)
  const clientTs = useRef(localIso())
  const worker = profile.display_name || 'मैं'
  const promptText = `अपना नाम बताइए, कि आप रिकॉर्डिंग के लिए राज़ी हैं, और ${worker} ने आपके साथ किन दिनों काम किया।`
  const tkName = profile.thekedar?.name

  useEffect(() => {
    alive.current = true
    if (profile.gps_opt_in) getFix({ timeoutMs: 10000 }).then((f) => { gpsRef.current = f })
    return () => { alive.current = false; stopSpeaking(); recRef.current?.cancel(); recRef.current = null }
  }, [profile.gps_opt_in])

  // Co-worker: the worker's confirmed days this month (cached copy works offline).
  useEffect(() => {
    if (isTk) return
    const d = new Date()
    const [from] = monthRange(d.getFullYear(), d.getMonth())
    const today = todayIso()
    const take = (led) => [...new Set([...(initialDates || []), ...((led?.days || []).map((x) => x.date))])].filter((x) => x <= today).sort().reverse()
    read(`cache:ledger:${from}`).then((c) => { if (c) setDays((cur) => cur || take(c)) })
    api.ledger(profile.worker_id, from, today).then((led) => setDays(take(led))).catch(() => setDays((cur) => cur || take(null)))
  }, [isTk, profile.worker_id])

  useEffect(() => {
    if (phase !== 'recording') return
    const t = setInterval(() => {
      if (!recRef.current) return
      const ms = Date.now() - recRef.current.started
      setElapsed(ms)
      setLevels((l) => [...l.slice(1), Math.max(0.08, levelRef.current)])
      if (ms >= MAX_MS) stop()
    }, 120)
    return () => clearInterval(t)
  }, [phase])

  function runCountdown(n) {
    return new Promise((resolve) => {
      if (!alive.current) return resolve()
      let left = n
      setCountdown(left)
      const t = setInterval(() => {
        left -= 1
        if (!alive.current || left <= 0) { clearInterval(t); setCountdown(null); resolve(); return }
        setCountdown(left)
      }, 1000)
    })
  }
  async function play(text, langCode) {
    const ok = await speakAsync(text, langCode)
    if (!ok && alive.current) await runCountdown(FALLBACK_S)
  }

  const recOpts = (echoCancellation) => ({
    maxMs: MAX_MS, echoCancellation,
    onLevel: (v) => { levelRef.current = v },
    onAutoStop: () => toast('60 सेकंड पूरे — रिकॉर्डिंग रुक गई'),
  })

  // Thekedar: the recorder starts before the notice so the notice itself is on the tape.
  async function startThekedar() {
    setPhase('notice')
    let rec
    try {
      rec = await startRecorder(recOpts(false))
    } catch {
      setPhase('error')
      return
    }
    if (!alive.current) { rec.cancel(); return }
    recRef.current = rec
    await play(NOTICE[lang].text, NOTICE[lang].lang)
    if (!alive.current || !recRef.current) return
    recRef.current.mark() // the notice ends here: on refusal only this part is kept
    setPhase('recording')
  }

  async function playPrompt() {
    setPhase('prompt')
    setPromptState('playing')
    await play(promptText, 'hi-IN')
    if (alive.current) setPromptState('done')
  }

  async function startCoworker() {
    stopSpeaking()
    try {
      const rec = await startRecorder(recOpts(true))
      if (!alive.current) { rec.cancel(); return }
      recRef.current = rec
      setPhase('recording')
    } catch {
      setPhase('error')
    }
  }

  async function stop() {
    const rec = recRef.current
    if (!rec) return
    recRef.current = null
    stopSpeaking()
    setPhase('saving')
    outRef.current = await rec.stop() // the mic is off now: Stop is instant
    setPhase('consent')
  }

  // refused: thekedar → keep only the notice part; co-worker → nothing is saved.
  async function save(refused = false) {
    const out = outRef.current
    if (refused && !isTk) { toast('कुछ सेव नहीं किया गया'); back(); return }
    const audio = refused ? out.noticeBlob : out.blob
    if (!audio || !audio.size) { toast('कुछ सेव नहीं किया गया'); back(); return }
    setPhase('saving')
    try {
      const r = await saveRecording({
        kind: isTk ? 'hisaab_statement' : 'coworker_confirm',
        speaker: who, noticePlayed: true, noticeLang: isTk ? lang : 'hi', consentRefused: refused,
        workerId: profile.worker_id, audio, photo: null,
        gps: profile.gps_opt_in ? gpsRef.current : null,
        clientTs: clientTs.current, durationS: out.durationS,
        extra: isTk ? {} : { dates: [...picked].sort() },
      })
      replace('saved', { localId: r.localId })
    } catch {
      setPhase('savefail')
      toast('फ़ोन में सेव नहीं हो पाया — फिर कोशिश करें')
    }
  }

  function cancel() {
    stopSpeaking()
    recRef.current?.cancel()
    recRef.current = null
    back()
  }

  const toggleDay = (d) => setPicked((s) => { const n = new Set(s); if (n.has(d)) n.delete(d); else n.add(d); return n })

  // ---- views ------------------------------------------------------------------------------------
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

  if (phase === 'savefail') {
    return (
      <div className="screen">
        <TopBar onCancel={cancel} speakText="फ़ोन में सेव नहीं हो पाया। फिर कोशिश करें।" />
        <h1 className="title">सेव नहीं हो पाया</h1>
        <p className="subtitle">रिकॉर्डिंग अभी इसी स्क्रीन में है। फिर से सेव करें।</p>
        <div className="bottom-actions"><Btn icon={Check} onClick={() => save(false)}>फिर सेव करें</Btn></div>
      </div>
    )
  }

  if (phase === 'lang') {
    return (
      <div className="screen">
        <TopBar title="ठेकेदार की बात" onBack={back} speakText="पहले फ़ोन ज़ोर से सूचना सुनाएगा कि बातचीत रिकॉर्ड हो रही है। सूचना किस भाषा में सुनानी है?" />
        <h1 className="title">सूचना किस भाषा में?</h1>
        <p className="subtitle">रिकॉर्ड से पहले फ़ोन ज़ोर से बताएगा कि बातचीत रिकॉर्ड हो रही है</p>
        <div className="stack">
          {Object.entries(NOTICE).map(([k, n]) => (
            <div key={k} className={`option ${lang === k ? 'on' : ''}`} onClick={() => setLang(k)} role="radio" aria-checked={lang === k}>
              <div className="body"><div className="name">{n.label}</div><div className="desc">“{n.text}”</div></div>
              <span className={`radio ${lang === k ? 'on' : ''}`}>{lang === k && <Check size={13} strokeWidth={3} />}</span>
            </div>
          ))}
        </div>
        <div className="info-row" style={{ marginTop: 14 }}>
          <Megaphone size={20} color="var(--brand)" /> सूचना हर बार सुनाई जाती है — इसे छोड़ा नहीं जा सकता। वे मना करें तो तुरंत रोकें।
        </div>
        <div className="bottom-actions">
          <Btn icon={Megaphone} onClick={startThekedar}>सूचना सुनाएँ और रिकॉर्ड शुरू करें</Btn>
        </div>
      </div>
    )
  }

  if (phase === 'notice') {
    return (
      <div className="screen">
        <TopBar onCancel={cancel} speakText={false} />
        <div className="card ask notice-card big" style={{ marginTop: 18 }}>
          <div className="h"><Megaphone size={20} /> पहले सूचना — हर बार, बंद नहीं होती</div>
          <div className="t">“{NOTICE[lang].text}”</div>
        </div>
        {countdown != null ? (
          <>
            <p className="center muted" style={{ marginTop: 22, marginBottom: 0 }}>ठेकेदार को यह सूचना पढ़कर सुनाएँ</p>
            <div className="countdown">{countdown}</div>
          </>
        ) : (
          <div className="row" style={{ justifyContent: 'center', marginTop: 26 }}><Spinner /> <b>फ़ोन सूचना बोल रहा है…</b></div>
        )}
        <div className="rec-state" style={{ marginTop: 22 }}><span className="rec-dot" /> रिकॉर्डिंग चालू — सूचना भी टेप पर आएगी</div>
        <div className="lock-note"><Volume2 size={16} /> फ़ोन की आवाज़ तेज़ रखें, ठेकेदार की तरफ़ रखें</div>
      </div>
    )
  }

  if (phase === 'days') {
    return (
      <div className="screen">
        <TopBar title="साथी की गवाही" onBack={back} speakText="किन दिनों साथी ने आपके साथ काम किया? दिन चुनें।" />
        <h1 className="title">किन दिनों साथ काम किया?</h1>
        <p className="subtitle">दिन चुनें — साथी इन्हीं दिनों की बात बोलेंगे</p>
        {days === null ? <div className="row"><Spinner /> दिन खोल रहे हैं…</div>
          : days.length === 0 ? <div className="info-row">इस महीने अभी कोई पक्का दिन नहीं — पहले अपना काम बोलकर पक्का करें।</div>
            : (
              <div className="stack">
                {days.map((d) => (
                  <div key={d} className={`option ${picked.has(d) ? 'on' : ''}`} style={{ minHeight: 56 }} onClick={() => toggleDay(d)} role="checkbox" aria-checked={picked.has(d)}>
                    <div className="body"><div className="name">{shortDayDate(d)}</div></div>
                    <span className={`check-box ${picked.has(d) ? 'on' : ''}`}>{picked.has(d) && <Check size={15} strokeWidth={3} />}</span>
                  </div>
                ))}
              </div>
            )}
        <div className="bottom-actions">
          <Btn onClick={playPrompt} disabled={picked.size === 0}>आगे बढ़ें{picked.size ? ` (${picked.size} दिन)` : ''}</Btn>
        </div>
      </div>
    )
  }

  if (phase === 'prompt') {
    return (
      <div className="screen">
        <TopBar title="साथी की गवाही" onBack={() => { stopSpeaking(); setPhase('days') }} speakText={false} />
        <p className="subtitle" style={{ marginTop: 8 }}>फ़ोन साथी को यह बात सुनाएगा:</p>
        <div className="say-card">
          <Quote size={20} />
          <p>‘{promptText}’</p>
        </div>
        <div className="small" style={{ marginTop: 10, color: 'var(--text-2)' }}>चुने दिन: {[...picked].sort().map(dayMonth).join(', ')}</div>
        <div style={{ marginTop: 14 }}>
          {promptState === 'done' ? <div className="notice-card" style={{ padding: 0 }}><div className="done"><CircleCheck size={20} /> सुना दी गई</div></div>
            : countdown != null ? <div className="row"><b>साथी को यह बात पढ़कर सुनाएँ</b><span className="countdown" style={{ fontSize: 28 }}>{countdown}</span></div>
              : <div className="row"><Spinner /> <b>सुना रहे हैं…</b></div>}
        </div>
        <div className="info-row" style={{ marginTop: 14 }}>साथी मना करें तो रिकॉर्ड न करें।</div>
        <div className="bottom-actions">
          <Btn variant="plain" icon={Volume2} disabled={promptState === 'playing'} onClick={playPrompt}>फिर से सुनाएँ</Btn>
          <Btn icon={Mic} disabled={promptState !== 'done'} onClick={startCoworker}>साथी राज़ी हैं — रिकॉर्ड शुरू करें</Btn>
        </div>
      </div>
    )
  }

  if (phase === 'consent') {
    return (
      <div className="screen">
        <TopBar title={isTk ? 'ठेकेदार की बात' : 'साथी की गवाही'} speakText={isTk ? 'क्या ठेकेदार ने रिकॉर्डिंग के लिए हाँ कहा?' : 'क्या साथी ने रिकॉर्डिंग के लिए हाँ कहा?'} />
        <div className="big-check"><span><Check size={30} strokeWidth={3} /></span></div>
        <h1 className="saved-title">{isTk ? 'ठेकेदार ने हाँ कहा?' : 'साथी ने हाँ कहा?'}</h1>
        <p className="center muted">रिकॉर्डिंग रुक गई है · {outRef.current?.durationS || 0} सेकंड</p>
        <div className="bottom-actions">
          <Btn icon={Check} onClick={() => save(false)}>हाँ — पूरी बातचीत सेव करें</Btn>
          <Btn variant="danger" onClick={() => save(true)}>{isTk ? 'मना किया — सिर्फ़ सूचना रखें' : 'मना किया — कुछ सेव न करें'}</Btn>
        </div>
      </div>
    )
  }

  // recording | saving (UI/ S6)
  const played = Math.round((Math.min(elapsed, MAX_MS) / MAX_MS) * BARS)
  return (
    <div className="screen">
      <TopBar onCancel={cancel} speakText={false} />
      {isTk ? (
        <div className="card ask notice-card">
          <div className="h"><Megaphone size={18} /> पहले सूचना — हर बार, बंद नहीं होती</div>
          <div className="t">“{NOTICE[lang].text}”</div>
          <div className="done"><CircleCheck size={20} /> सुना दी गई</div>
        </div>
      ) : (
        <div className="card ask notice-card">
          <div className="h"><Megaphone size={18} /> सहमति पूछी गई</div>
          <div className="done"><CircleCheck size={20} /> सुना दी गई · {picked.size} दिन</div>
        </div>
      )}
      <div className="other-title">{isTk ? (tkName ? `${tkName} जी का जवाब` : 'ठेकेदार का जवाब') : 'साथी की गवाही'}</div>
      <div className="rec-state"><span className="rec-dot" /> रिकॉर्ड हो रहा है</div>
      <div className="ask-line">{isTk ? 'ठेकेदार से पूछें: ‘रिकॉर्ड कर रहे हैं, ठीक है?’' : 'साथी बोलें: नाम, ‘हाँ, रिकॉर्ड कर सकते हैं’, और किन दिनों साथ काम किया'}</div>
      <div className="timer sm">{mmss(elapsed)} / {mmss(MAX_MS)}</div>
      <div className="rec-bar"><i style={{ width: `${Math.min(100, (elapsed / MAX_MS) * 100)}%` }} /></div>
      <div className="wave red" aria-hidden>
        {levels.map((v, i) => <i key={i} className={i < played ? 'on' : ''} style={{ height: `${Math.round(8 + SHAPE[i] * (16 + Math.min(1, v * 1.6) * 30))}px` }} />)}
      </div>
      <div className="stop-wrap" style={{ marginTop: 6 }}>
        <button className="stop-btn" onClick={stop} disabled={phase !== 'recording'} aria-label="रोकें">
          <span><b /></span>
        </button>
        <div className="stop-label">{phase === 'saving' ? 'सेव हो रहा है…' : 'रोकें'}</div>
      </div>
      <div className="lock-note"><Lock size={16} /> {isTk ? 'वे मना करें तो तुरंत रोकें — सूचना के अलावा कुछ सेव नहीं होगा' : 'साथी मना करें तो तुरंत रोकें — कुछ सेव नहीं होगा'}</div>
    </div>
  )
}
