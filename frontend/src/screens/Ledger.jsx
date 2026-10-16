// Ledger / खाता (UI/ H1): month calendar, day-wise list, chain record code.
import { useEffect, useRef, useState } from 'react'
import { Camera, Check, ChevronLeft, ChevronRight, Circle, Link2, MapPin, Mic, ShieldCheck, CircleAlert, Users, User } from 'lucide-react'
import { Btn, Sheet, TabBar, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { read, write } from '../lib/db.js'
import { WD_LETTER, clock12, hoursText, localIso, monthName, monthRange, rupees, shortDayDate, todayIso, workedMinutes } from '../lib/format.js'
import { shortCode } from '../lib/hash.js'
import { savePhoto } from '../lib/sync.js'

// Corroboration ladder (BUILD_PLAN P3): L1 own entry, L2 + photo/GPS at site, L3 + co-worker or thekedar.
const SIGNALS = [
  ['SELF', 'आपकी पक्की एंट्री'], ['PHOTO', 'उस दिन की फ़ोटो'], ['GPS_AT_SITE', 'साइट पर GPS'],
  ['COWORKER', 'साथी की गवाही'], ['THEKEDAR_ACK', 'ठेकेदार ने माना'],
]
function CorrBadge({ c }) {
  const level = c?.level || 1
  if (level >= 3) return <span className="chip ok sm"><Users size={15} /> L3 · गवाह</span>
  if (level === 2) return <span className="chip blue sm"><MapPin size={15} /> L2 · साइट</span>
  return <span className="chip neutral sm"><User size={15} /> L1 · अपना</span>
}

export default function Ledger() {
  const { profile, go, toast } = useApp()
  const [open, setOpen] = useState(null) // date shown in the sheet
  const [proofFor, setProofFor] = useState(null)
  const fileRef = useRef(null)
  const now = new Date()
  const [ym, setYm] = useState([now.getFullYear(), now.getMonth()])
  const [filter, setFilter] = useState('all')
  const [data, setData] = useState(null)
  const [chain, setChain] = useState(null)
  const today = todayIso()
  const [from, to] = monthRange(ym[0], ym[1])
  const cacheKey = `cache:ledger:${from}`

  useEffect(() => {
    let alive = true
    read(cacheKey).then((c) => { if (alive && c) setData(c) })
    api.ledger(profile.worker_id, from, to).then((d) => { if (alive) { setData(d); write(cacheKey, d) } }).catch(() => {})
    api.chainVerify().then((c) => alive && setChain(c)).catch(() => {})
    return () => { alive = false }
  }, [from, to, profile.worker_id, cacheKey])

  const days = data?.days || []
  const pays = data?.payments || []
  const dayMap = Object.fromEntries(days.map((d) => [d.date, d]))
  const payByDate = pays.reduce((m, p) => ({ ...m, [p.date]: (m[p.date] || 0) + Number(p.amount || 0) }), {})
  const paysOn = (iso) => pays.filter((p) => p.date === iso)

  function addProof(p) {
    setProofFor(p)
    fileRef.current?.click()
  }
  async function onProof(e) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f || !proofFor) return
    try {
      const r = await savePhoto({ workerId: profile.worker_id, kind: 'payment_proof', photo: f, entryId: proofFor.entry_id, clientTs: localIso() })
      toast(`रसीद सेव ✓ #${shortCode(r.sha256, 2)}`)
      setOpen(null)
    } catch {
      toast('फ़ोटो सेव नहीं हो पाई — फिर कोशिश करें')
    }
  }

  const first = new Date(ym[0], ym[1], 1)
  const lead = (first.getDay() + 6) % 7
  const nDays = new Date(ym[0], ym[1] + 1, 0).getDate()
  const cells = [...Array(lead).fill(null), ...Array.from({ length: nDays }, (_, i) => `${from.slice(0, 8)}${String(i + 1).padStart(2, '0')}`)]

  const listDates = [...new Set([...(filter !== 'money' ? days.map((d) => d.date) : []), ...(filter !== 'work' ? Object.keys(payByDate) : [])])]
    .filter(Boolean).sort().reverse()

  const shift = (n) => setYm(([y, m]) => { const d = new Date(y, m + n, 1); return [d.getFullYear(), d.getMonth()] })

  return (
    <div className="screen with-tabs">
      <TopBar title="खाता" speakText={`खाता। ${monthName(ym[1])} में ${days.length} दिन का काम पक्का है।`} />
      <div className="month-nav">
        <button className="round" onClick={() => shift(-1)} aria-label="पिछला महीना"><ChevronLeft size={22} /></button>
        <div className="t">{monthName(ym[1])} {ym[0]}</div>
        <button className="round" onClick={() => shift(1)} aria-label="अगला महीना"><ChevronRight size={22} /></button>
      </div>
      <div className="toggle-chips">
        {[['all', 'सब'], ['work', 'काम'], ['money', 'पैसा']].map(([v, l]) => (
          <button key={v} className={`tchip ${filter === v ? 'on' : ''}`} onClick={() => setFilter(v)}>{l}</button>
        ))}
      </div>

      <div className="card cal">
        <div className="cal-grid">
          {WD_LETTER.map((w) => <div key={w} className="wd">{w}</div>)}
          {cells.map((iso, i) => iso === null ? <div key={`x${i}`} /> : (
            <div key={iso}>
              <div className={`cal-day ${dayMap[iso] && filter !== 'money' ? 'done' : ''} ${iso === today ? 'today' : ''}`}>
                {Number(iso.slice(8))}
                {payByDate[iso] && filter !== 'work' && <span className="rs">₹</span>}
              </div>
            </div>
          ))}
        </div>
        <div className="cal-legend">
          <span><i /> काम पक्का</span><span><i className="fill" /> ₹ पैसा मिला</span><span><i /> आज</span>
        </div>
      </div>

      <div className="label" style={{ fontSize: 17, color: 'var(--text)', marginTop: 18 }}>दिन-वार</div>
      <div className="day-list">
        {listDates.length === 0 && <div className="muted">इस महीने अभी कोई पक्की एंट्री नहीं</div>}
        {listDates.map((iso) => {
          const d = dayMap[iso]
          const mins = d ? workedMinutes(d.start_time, d.end_time, d.break_minutes) : null
          const parts = []
          if (d) parts.push(`${clock12(d.start_time)} – ${clock12(d.end_time)}`, hoursText(mins))
          if (payByDate[iso]) parts.push(`${rupees(payByDate[iso])} मिला`)
          const proofs = paysOn(iso).reduce((t, p) => t + (p.proof_photos || 0), 0)
          return (
            <button key={iso} className="drow tap" onClick={() => setOpen(iso)}>
              <div className="grow">
                <div className="dt">{shortDayDate(iso)}</div>
                <div className="ds">{parts.join(' · ')}</div>
              </div>
              <div className="chips">
                {d && <CorrBadge c={d.corroboration} />}
                {d?.corroboration?.flags?.includes('THEKEDAR_DISPUTES') && <span className="chip urgent sm"><CircleAlert size={15} /> ठेकेदार असहमत</span>}
                {proofs > 0 && <span className="chip ok sm">रसीद ✓</span>}
              </div>
            </button>
          )
        })}
      </div>
      {data?.corroboration_note?.hi && <p className="small" style={{ margin: '8px 0 0', color: 'var(--text-2)' }}>{data.corroboration_note.hi}</p>}
      <input ref={fileRef} className="hidden-input" type="file" accept="image/*" capture="environment" onChange={onProof} />

      <div className="card soft code-card">
        <Link2 size={22} color="var(--text-2)" />
        <div className="c">रिकॉर्ड कोड <span style={{ whiteSpace: 'nowrap' }}>{chain?.head?.short || data?.chain_head?.short || '—'}</span></div>
        {chain && (chain.ok
          ? <span className="ok"><ShieldCheck size={20} /> सब सही</span>
          : <span className="ok" style={{ color: 'var(--urgent)' }}><CircleAlert size={20} /> जाँचें</span>)}
      </div>
      <DaySheet iso={open} day={open ? dayMap[open] : null} pays={open ? paysOn(open) : []} onClose={() => setOpen(null)}
        onCoworker={(iso) => go('recordOther', { who: 'coworker', dates: [iso] })} onProof={addProof} />
      <TabBar active="ledger" />
    </div>
  )
}


function DaySheet({ iso, day, pays, onClose, onCoworker, onProof }) {
  if (!iso) return null
  const sig = new Set(day?.corroboration?.signals || [])
  const disputed = day?.corroboration?.flags?.includes('THEKEDAR_DISPUTES')
  return (
    <Sheet open onClose={onClose}>
      <h2>{shortDayDate(iso)}</h2>
      {day && (
        <>
          <div className="row" style={{ margin: '4px 0 6px' }}><CorrBadge c={day.corroboration} /></div>
          {SIGNALS.map(([k, l]) => (
            <div key={k} className={`sig ${sig.has(k) ? '' : 'off'}`}>
              {sig.has(k) ? <span className="tick-dot"><Check size={15} strokeWidth={3} /></span> : <Circle size={24} color="var(--border)" />}
              {l}
            </div>
          ))}
          {disputed && <div className="info-row" style={{ background: 'var(--urgent-bg)', color: 'var(--urgent)', marginTop: 6 }}><CircleAlert size={20} /> ठेकेदार ने यह दिन नहीं माना</div>}
        </>
      )}
      {pays.map((p) => (
        <div key={p.entry_id} className="row between" style={{ marginTop: 10 }}>
          <b>{rupees(p.amount)} मिला</b>
          {p.proof_photos > 0 && <span className="chip ok sm">रसीद ✓</span>}
        </div>
      ))}
      <div className="stack" style={{ marginTop: 14 }}>
        {day && <Btn variant="outline" icon={Mic} onClick={() => onCoworker(iso)}>साथी से पुष्टि कराएँ</Btn>}
        {pays.map((p) => (
          <Btn key={p.entry_id} variant="outline" icon={Camera} onClick={() => onProof(p)}>
            रसीद की फ़ोटो जोड़ें{pays.length > 1 ? ` (${rupees(p.amount)})` : ''}
          </Btn>
        ))}
        <Btn variant="plain" onClick={onClose}>बंद करें</Btn>
      </div>
    </Sheet>
  )
}
