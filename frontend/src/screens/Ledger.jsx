// Ledger / खाता (UI/ H1): month calendar, day-wise list, chain record code.
import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, Link2, ShieldCheck, CircleAlert } from 'lucide-react'
import { StatusChip, TabBar, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { read, write } from '../lib/db.js'
import { WD_LETTER, clock12, hoursText, monthName, monthRange, rupees, shortDayDate, todayIso, workedMinutes } from '../lib/format.js'

export default function Ledger() {
  const { profile } = useApp()
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
          return (
            <div key={iso} className="drow">
              <div className="grow">
                <div className="dt">{shortDayDate(iso)}</div>
                <div className="ds">{parts.join(' · ')}</div>
              </div>
              <StatusChip status="green" />
            </div>
          )
        })}
      </div>

      <div className="card soft code-card">
        <Link2 size={22} color="var(--text-2)" />
        <div className="c">रिकॉर्ड कोड <span style={{ whiteSpace: 'nowrap' }}>{chain?.head?.short || data?.chain_head?.short || '—'}</span></div>
        {chain && (chain.ok
          ? <span className="ok"><ShieldCheck size={20} /> सब सही</span>
          : <span className="ok" style={{ color: 'var(--urgent)' }}><CircleAlert size={20} /> जाँचें</span>)}
      </div>
      <TabBar active="ledger" />
    </div>
  )
}

