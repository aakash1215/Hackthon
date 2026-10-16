// वादा (UI/ S7 clone). The thekedar's words come verbatim from the inbox item; the amount and the
// date are saved only after the worker confirms them here (hard rule 3). The date is never guessed
// silently: a weekday word preselects a date, but it stays amber until the worker picks it.
import { useEffect, useMemo, useState } from 'react'
import { BellRing, CalendarClock, Check, CircleAlert, Handshake, IndianRupee, Pencil, Quote } from 'lucide-react'
import { Btn, Sheet, StatusChip, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { addDays, dayMonth, longDate, rupees, todayIso, weekdayFromWords, weekdayName, weekdayOf } from '../lib/format.js'

export default function PromiseScreen({ item }) {
  const { profile, back, toast } = useApp()
  const tn = profile.thekedar?.name || item?.thekedar_name
  const name = tn ? `${tn} जी` : 'ठेकेदार'
  const days = useMemo(() => Array.from({ length: 14 }, (_, i) => addDays(todayIso(), i)), [])
  const guessed = useMemo(() => {
    const wd = weekdayFromWords(item?.date_text)
    if (wd == null) return null
    return days.slice(1).find((d) => weekdayOf(d) === wd) || null
  }, [days, item])
  const [amount, setAmount] = useState(item?.amount ?? null)
  const [amountOk, setAmountOk] = useState(item?.amount != null)
  const [due, setDue] = useState(guessed)
  const [dueOk, setDueOk] = useState(false)
  const [remind, setRemind] = useState(true)
  const [sheet, setSheet] = useState(null)
  const [past, setPast] = useState([])
  const [saving, setSaving] = useState(false)
  const done = item && item.status !== 'new' && item.status !== 'seen'

  useEffect(() => {
    api.promises(profile.worker_id).then((r) => setPast((r.items || []).filter((p) => p.confirmed !== false))).catch(() => {})
  }, [profile.worker_id])

  if (!item) {
    return (
      <div className="screen">
        <TopBar title="वादा" onBack={back} speakText="वादा" />
        <div className="info-row" style={{ marginTop: 12 }}><CircleAlert size={20} /> यह वादा नहीं मिला</div>
      </div>
    )
  }

  async function save() {
    if (amount == null) { setSheet('amount'); return }
    if (!due || !dueOk) { toast('कब तक — पक्का करें'); setSheet('date'); return }
    setSaving(true)
    try {
      const r = await api.inboxAction(item.id, { action: 'confirm', amount, due_date: due, remind })
      if (remind && 'Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(() => {})
      }
      toast(`वादा सेव हुआ${r.chain_head?.short ? ` · कोड ${r.chain_head.short}` : ''}`)
      back()
    } catch (e) {
      toast(e instanceof api.NetworkError ? 'हब से नहीं जुड़ पाए — बाद में सेव करें' : `सेव नहीं हुआ (${e.code})`)
    } finally {
      setSaving(false)
    }
  }

  const amtStatus = amount == null ? 'red' : amountOk ? 'green' : 'amber'
  const dueStatus = !due ? 'red' : dueOk ? 'green' : 'amber'
  const speakText = `${name} ने कहा: ${item.text}। रक़म ${amount != null ? `${amount} रुपये` : 'बतानी है'}। ${due ? `${longDate(due)} तक।` : ''} आप पक्का करेंगी, तभी सेव होगा।`

  return (
    <div className="screen">
      <TopBar title="वादा" onBack={back} speakText={speakText} />
      <div className="hero-bubble"><Handshake size={24} /></div>
      <h1 className="hero-title">जवाब में वादा मिला</h1>
      <p className="hero-sub">आप पक्का करेंगी, तभी सेव होगा</p>

      <div className="quote lg">
        <div className="q"><Quote size={16} /> {name} ने कहा:</div>
        <p>“{item.text}”</p>
      </div>

      <div className="card fields">
        <button className={`frow ${amtStatus === 'red' ? 'urgent' : amtStatus === 'amber' ? 'ask' : ''}`} onClick={() => !done && setSheet('amount')}>
          <span className={`icon-bubble ${amtStatus !== 'green' ? 'white' : ''}`}><IndianRupee size={18} /></span>
          <div className="grow">
            <div className="fl">रक़म</div>
            <div className={`fv ${amount == null ? 'muted' : ''}`}>{amount != null ? rupees(amount) : 'बताना है'}</div>
          </div>
          <StatusChip status={amtStatus} />
        </button>
        <button className={`frow ${dueStatus === 'red' ? 'urgent' : dueStatus === 'amber' ? 'ask' : ''}`} onClick={() => !done && setSheet('date')}>
          <span className={`icon-bubble ${dueStatus !== 'green' ? 'white' : ''}`}><CalendarClock size={18} /></span>
          <div className="grow">
            <div className="fl">कब तक</div>
            <div className={`fv ${due ? '' : 'muted'}`}>{due ? longDate(due) : item.date_text ? `“${item.date_text}” — चुनें` : 'बताना है'}</div>
          </div>
          <StatusChip status={dueStatus} />
        </button>
      </div>

      <div className="remind-row">
        <BellRing size={22} />
        <span className="grow">{due ? `${weekdayName(due)} सुबह 9 बजे याद दिलाएँगे` : 'सुबह 9 बजे याद दिलाएँगे'}</span>
        <button className={`switch ${remind ? 'on' : ''}`} role="switch" aria-checked={remind} aria-label="याद दिलाएँ" onClick={() => setRemind((v) => !v)} />
      </div>

      {past.length > 0 && (
        <>
          <div className="label">पिछले वादे</div>
          <div className="card">
            {past.slice(0, 5).map((p) => (
              <div key={p.id} className="past-row">
                <span>{rupees(p.amount)}{p.due_date ? ` · ${dayMonth(p.due_date)} तक` : ''}</span>
                <span className="chip neutral sm">वादा</span>
              </div>
            ))}
          </div>
        </>
      )}

      {done ? (
        <div className="info-row" style={{ marginTop: 12 }}><Check size={20} color="var(--brand)" /> यह वादा पहले ही सेव हो चुका है।</div>
      ) : (
        <div className="bottom-actions">
          <div className="btn-row">
            <Btn variant="outline" className="narrow" icon={Pencil} onClick={() => setSheet('amount')}>बदलें</Btn>
            <Btn icon={Check} onClick={save} disabled={saving}>{saving ? 'सेव…' : 'सही है, सेव करें'}</Btn>
          </div>
        </div>
      )}

      {sheet === 'amount' && (
        <AmountSheet value={amount} onClose={() => setSheet(null)} onPick={(v) => { setAmount(v); setAmountOk(v != null); setSheet(null) }} />
      )}
      <Sheet open={sheet === 'date'} onClose={() => setSheet(null)}>
        <h2>कब तक देंगे?</h2>
        {item.date_text && <p className="muted" style={{ marginTop: 0 }}>{name} ने कहा “{item.date_text}”। सही दिन चुनें।</p>}
        <div className="stack" style={{ marginTop: 8 }}>
          {days.map((d, i) => {
            const on = due === d
            return (
              <div key={d} className={`option ${on ? 'on' : ''}`} style={{ minHeight: 52 }} role="radio" aria-checked={on}
                onClick={() => { setDue(d); setDueOk(true); setSheet(null) }}>
                <div className="body">
                  <div className="name">{longDate(d)}</div>
                  {(i < 2 || d === guessed) && <div className="desc">{[i === 0 ? 'आज' : i === 1 ? 'आने वाला कल' : null, d === guessed ? `“${item.date_text}” से मेल` : null].filter(Boolean).join(' · ')}</div>}
                </div>
                <span className={`radio ${on ? 'on' : ''}`}>{on && <Check size={13} strokeWidth={3} />}</span>
              </div>
            )
          })}
        </div>
      </Sheet>
    </div>
  )
}

function AmountSheet({ value, onClose, onPick }) {
  const [draft, setDraft] = useState(value)
  return (
    <Sheet open onClose={onClose}>
      <h2>वादे की रक़म</h2>
      <div className="field" style={{ marginTop: 10 }}>
        <span style={{ fontWeight: 700, fontSize: 20 }}>₹</span>
        <input inputMode="numeric" autoFocus value={draft ?? ''} onChange={(e) => { const d = e.target.value.replace(/\D/g, '').slice(0, 6); setDraft(d ? Number(d) : null) }} />
      </div>
      <div className="btn-row" style={{ marginTop: 16 }}>
        <Btn variant="plain" className="narrow" onClick={onClose}>रद्द</Btn>
        <Btn icon={Check} onClick={() => onPick(draft)} disabled={draft == null}>यही सही है</Btn>
      </div>
    </Sheet>
  )
}
