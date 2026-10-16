// Saved (UI/ D3): shows the save code at once, then processes on the hub when it is reachable.
import { useEffect, useRef, useState } from 'react'
import { Check, CircleAlert, Fingerprint, MapPin, ShieldCheck } from 'lucide-react'
import { Btn, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { getRecords, updateRecord } from '../lib/db.js'
import { speak } from '../lib/device.js'
import { dayMonth } from '../lib/format.js'
import { shortCode } from '../lib/hash.js'
import { flush } from '../lib/sync.js'
import { readbackText } from './Confirm.jsx'

const UNDERSTAND = {
  workday: 'समय, ठेकेदार, साथी पहचान रहे हैं (1–2 मिनट)',
  payment: 'रक़म, तारीख, देने वाला पहचान रहे हैं (1–2 मिनट)',
  hisaab_statement: 'दिन, दर, कटौती, दी गई रक़म पहचान रहे हैं (1–2 मिनट)',
  coworker_confirm: 'साथी का नाम, दिन, साइट पहचान रहे हैं (1–2 मिनट)',
}
const SAVED_TITLE = { hisaab_statement: 'हिसाब की बात सुरक्षित', coworker_confirm: 'गवाही सुरक्षित' }

export default function Saved({ localId }) {
  const { sync, reset, replace } = useApp()
  const [rec, setRec] = useState(null)
  const [proc, setProc] = useState({ state: 'idle' }) // idle | running | done | error
  const started = useRef(false)

  useEffect(() => {
    let alive = true
    const load = () => getRecords().then((all) => { if (alive) setRec(all[localId] || null) })
    load()
    const t = setInterval(load, 1000)
    flush()
    return () => { alive = false; clearInterval(t) }
  }, [localId])

  useEffect(() => {
    if (!rec?.serverId || started.current || rec.status === 'hash_mismatch' || rec.consentRefused) return
    if (rec.status === 'processed') { setProc({ state: 'done' }); return }
    started.current = true
    setProc({ state: 'running' })
    api.processEntry(rec.serverId).then(async (r) => {
      if (r.status === 'processed') {
        await updateRecord(localId, { status: 'processed' })
        setProc({ state: 'done', fields: r.fields })
        speak(readbackText(rec.kind, r.fields))
      } else {
        setProc({ state: 'error', code: r.error })
      }
    }).catch((e) => { started.current = false; setProc({ state: 'error', code: e.code || 'NETWORK' }) })
  }, [rec?.serverId, rec?.status, localId, rec?.kind])

  if (!rec) return <div className="screen" />
  const uploaded = !!rec.serverId
  const offline = !sync.online || sync.hub === false

  const step2 = proc.state === 'done' ? 'done' : uploaded && proc.state === 'running' ? 'active' : 'todo'
  const step3 = proc.state === 'done' ? 'active' : 'todo'

  return (
    <div className="screen">
      <TopBar speakText={`आवाज़ सुरक्षित। सेव कोड ${shortCode(rec.sha256, 2)}`} />
      <div className="big-check"><span><Check size={34} strokeWidth={3} /></span></div>
      <h1 className="saved-title">{SAVED_TITLE[rec.kind] || 'आवाज़ सुरक्षित'}</h1>
      <div className="center muted">{dayMonth(rec.createdAt.slice(0, 10))} · {rec.durationS || 0} सेकंड</div>
      <div className="code-pill"><Fingerprint size={22} /> सेव कोड&nbsp; {shortCode(rec.sha256, 2)}</div>
      {rec.gps && <div className="center" style={{ marginTop: -8, marginBottom: 12 }}><span className="gps-chip"><MapPin size={16} /> {rec.gps.lat.toFixed(5)}, {rec.gps.lon.toFixed(5)}</span></div>}

      <div className="card steps">
        <div className="step done">
          <span className="dot"><Check size={13} strokeWidth={3} /></span>
          <div><div className="t">सुना</div><div className="d">{uploaded ? (rec.hashMatch ? 'हब पर पहुँची · कोड मेल खाया ✓' : 'हब पर पहुँची') : 'आवाज़ फ़ोन में सेव हो गई'}</div></div>
        </div>
        <div className={`step ${step2}`}>
          <span className="dot">{step2 === 'done' && <Check size={13} strokeWidth={3} />}</span>
          <div>
            <div className="t">समझ रहे हैं…</div>
            <div className="d">
              {!uploaded ? (offline ? 'हब से जुड़ने पर समझेंगे' : 'हब पर भेज रहे हैं…')
                : proc.state === 'error' ? `अभी समझ नहीं पाए (${proc.code}) — बाद में फिर कोशिश होगी`
                  : UNDERSTAND[rec.kind] || UNDERSTAND.workday}
            </div>
          </div>
        </div>
        <div className={`step ${step3}`}>
          <span className="dot" />
          <div><div className="t">पढ़कर सुनाएँगे</div><div className="d">फिर आप पक्का करेंगी</div></div>
        </div>
      </div>

      {rec.consentRefused ? (
        <div className="info-row" style={{ marginTop: 12, color: 'var(--text)' }}>
          <ShieldCheck size={24} color="var(--brand)" /> मना किया गया — सिर्फ़ रिकॉर्डिंग की सूचना सेव हुई, बातचीत नहीं। इसे समझा या पक्का नहीं किया जाएगा।
        </div>
      ) : rec.status === 'hash_mismatch' ? (
        <div className="info-row" style={{ marginTop: 12, background: 'var(--urgent-bg)', color: 'var(--urgent)' }}>
          <CircleAlert size={22} /> हब पर पहुँची फ़ाइल का कोड मेल नहीं खाया। यह दर्ज कर लिया गया है — यूनियन/सहायक को बताएँ।
        </div>
      ) : (
        <div className="info-row" style={{ marginTop: 12, color: 'var(--text)' }}>
          <ShieldCheck size={24} color="var(--brand)" /> फ़ोन बंद हो जाए तो भी आवाज़ सेव है। बाद में समझ लेंगे।
        </div>
      )}

      <div className="bottom-actions">
        {proc.state === 'done' && <Btn icon={Check} onClick={() => replace('confirm', { entryId: rec.serverId, localId })}>पक्का करें</Btn>}
        <Btn variant="plain" onClick={() => reset('home')}>बाद में देखेंगे</Btn>
      </div>
    </div>
  )
}
