// Confirm card (UI/ D4 workday, D5 "which day?" sheet, D6 payment). Colours come from the hub's
// reconciler; a value the worker picks becomes green. Only confirmed values are sent to the engine.
import { useEffect, useState } from 'react'
import {
  Banknote, CalendarCheck, CalendarClock, CalendarDays, CalendarRange, Check, CircleAlert, CircleCheck, CircleHelp,
  CircleMinus, Clock, Coffee, HardHat, IndianRupee, MapPin, MessageSquare, Pencil, Quote, Scale, Sigma, Timer, Users,
  Volume2, Wallet,
} from 'lucide-react'
import { Btn, Sheet, Spinner, StatusChip, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { getRecords, updateRecord } from '../lib/db.js'
import { speak } from '../lib/device.js'
import { addDays, clockLong, dayMonth, hoursText, longDate, rupees, todayIso, workedMinutes } from '../lib/format.js'

const breakText = (v) => (v == null || v === '' ? null : Number(v) === 0 ? 'कोई नहीं' : Number(v) % 60 === 0 ? `${Number(v) / 60} घंटा` : `${v} मिनट`)
const dateText = (v) => {
  if (!v) return null
  const t = todayIso()
  return `${dayMonth(v)}${v === t ? ' (आज)' : v === addDays(t, -1) ? ' (कल)' : ''}`
}

const WORKDAY_ROWS = [
  { name: 'work_date', label: 'तारीख', icon: CalendarDays, fmt: dateText, editor: 'date', required: true },
  { name: 'start_time', label: 'काम शुरू', icon: Clock, fmt: clockLong, editor: 'time', required: true },
  { name: 'end_time', label: 'काम ख़त्म', icon: Clock, fmt: clockLong, editor: 'time', required: true },
  { name: 'break_minutes', label: 'आराम (रोज़ का)', icon: Coffee, fmt: breakText, editor: 'break', required: true },
  { name: 'contractor_name', label: 'ठेकेदार', icon: HardHat, editor: 'text', empty: 'नहीं बताया' },
  { name: 'coworkers_present', label: 'साथ में', icon: Users, editor: 'text', empty: 'नहीं बताया' },
]
const PAYMENT_ROWS = [
  { name: 'payment_date', label: 'तारीख', icon: CalendarDays, fmt: dateText, editor: 'date', required: true },
  { name: 'payer_name', label: 'किसने दिया', icon: HardHat, editor: 'text', empty: 'नहीं बताया' },
  { name: 'covers_from', label: 'किस काम का', icon: CalendarRange, editor: 'text', empty: 'नहीं बताया' },
  { name: 'deductions', label: 'कोई कटौती?', icon: CircleMinus, editor: 'text', empty: 'कुछ नहीं बताया' },
]
const MODES = [['cash', 'नकद'], ['upi', 'UPI'], ['bank', 'बैंक']]

// P3: what the thekedar said (BUILD_PLAN §8) and a co-worker's confirmation (§9). All numbers optional.
const STATEMENT_NUMS = ['days_counted', 'rate_per_day', 'gross_amount', 'deductions', 'paid_now', 'balance_promised']
const STATEMENT_ROWS = [
  { name: 'days_counted', label: 'काम के दिन', icon: CalendarDays, fmt: (v) => `${v} दिन`, editor: 'number' },
  { name: 'rate_per_day', label: 'रोज़ की दर', icon: IndianRupee, fmt: rupees, editor: 'amount' },
  { name: 'gross_amount', label: 'कुल', icon: Sigma, fmt: rupees, editor: 'amount' },
  { name: 'deductions', label: 'उचल / कटौती', icon: CircleMinus, fmt: rupees, editor: 'amount' },
  { name: 'paid_now', label: 'कितना दिया', icon: Banknote, fmt: rupees, editor: 'amount' },
  { name: 'balance_promised', label: 'बाकी देने को कहा', icon: Wallet, fmt: rupees, editor: 'amount' },
  { name: 'promised_date', label: 'कब देंगे', icon: CalendarClock, editor: 'text', empty: 'नहीं बताया' },
]
const INTENTS = [['acknowledges', 'दिन माने'], ['promise_to_pay', 'पैसे देने का वादा'], ['disputes_days', 'दिन नहीं माने'], ['other', 'पता नहीं']]
const INTENT_LABEL = Object.fromEntries(INTENTS)
const INTENT_ROW = { name: 'intent', label: 'ठेकेदार ने क्या कहा', icon: MessageSquare, fmt: (v) => INTENT_LABEL[v] || v, editor: 'intent', required: true }
const datesFmt = (v) => (Array.isArray(v) && v.length ? [...v].sort().map(dayMonth).join(', ') : null)
const COWORKER_ROWS = [
  { name: 'coworker_name', label: 'साथी का नाम', icon: Users, editor: 'text' },
  { name: 'dates', label: 'किन दिनों साथ काम किया', icon: CalendarCheck, fmt: datesFmt, editor: 'dates', required: true },
  { name: 'dates_or_days', label: 'साथी ने दिन क्या बताए', icon: Quote, editor: 'text', empty: 'नहीं सुना' },
  { name: 'site', label: 'साइट', icon: MapPin, editor: 'text', empty: 'नहीं बताया' },
  { name: 'consent_phrase', label: 'हाँ के शब्द', icon: Quote, editor: 'text', empty: 'नहीं सुना' },
]
const isEmpty = (v) => v == null || v === '' || (Array.isArray(v) && v.length === 0)

/** Read-back template, filled only with candidate values; unknowns are spoken as unknown (Handoff §10.12). */
export function readbackText(kind, fields) {
  const v = (n) => {
    const f = fields?.[n]
    if (!f) return null
    if (f.value !== undefined && f.value !== null && f.value !== '') return f.value
    return f.candidates?.length === 1 ? f.candidates[0] : null
  }
  const unk = 'पता नहीं'
  if (kind === 'hisaab_statement') {
    const r = (n) => (v(n) != null ? `${v(n)} रुपये` : unk)
    return `काम के दिन: ${v('days_counted') ?? unk}। रोज़ की दर: ${r('rate_per_day')}। कटौती: ${r('deductions')}। कितना दिया: ${r('paid_now')}। क्या यह सही है?`
  }
  if (kind === 'coworker_confirm') return `साथी का नाम: ${v('coworker_name') || unk}। क्या यह सही है?`
  if (kind === 'payment') {
    return `मिली रक़म: ${v('amount_paid') != null ? `${v('amount_paid')} रुपये` : unk}। तारीख: ${v('payment_date') ? dayMonth(v('payment_date')) : unk}। क्या यह सही है?`
  }
  return `तारीख: ${v('work_date') ? dayMonth(v('work_date')) : unk}। काम शुरू: ${v('start_time') ? clockLong(v('start_time')) : unk}। काम ख़त्म: ${v('end_time') ? clockLong(v('end_time')) : unk}। आराम: ${breakText(v('break_minutes')) || unk}। क्या यह सही है?`
}

export default function Confirm({ entryId, localId, copied }) {
  const { profile, back, reset, replace, go, toast } = useApp()
  const [entry, setEntry] = useState(null)
  const [fields, setFields] = useState({})
  const [vals, setVals] = useState({})
  const [touched, setTouched] = useState({})
  const [phase, setPhase] = useState('loading') // loading | processing | ready | blocked | done | error
  const [blockCode, setBlockCode] = useState(null)
  const [sheet, setSheet] = useState(null)
  const [saving, setSaving] = useState(false)
  const [dayOptions, setDayOptions] = useState([])

  function init(e, f, reply) {
    const ff = { ...(f || {}) }
    const v = {}
    for (const [name, fld] of Object.entries(f || {})) {
      v[name] = fld.value ?? (fld.candidates?.length === 1 ? fld.candidates[0] : null)
    }
    if (e.kind === 'workday' && !v.contractor_name && profile.thekedar?.name) v.contractor_name = profile.thekedar.name
    if (e.kind === 'payment' && !v.payer_name && profile.thekedar?.name) v.payer_name = profile.thekedar.name
    // Thekedar's intent: the classifier's guess is only a suggestion (amber) until the worker picks.
    if (e.kind === 'hisaab_statement' && e.speaker === 'thekedar' && v.intent == null && reply?.intent && INTENT_LABEL[reply.intent]) {
      v.intent = reply.intent
      ff.intent = { status: 'amber' }
    }
    setFields(ff)
    setVals(v)
    if (e.kind === 'coworker_confirm') {
      getRecords().then((all) => {
        const rec = (localId && all[localId]) || Object.values(all).find((x) => x.serverId === entryId)
        if (rec?.dates?.length) setVals((cur) => (isEmpty(cur.dates) ? { ...cur, dates: rec.dates } : cur))
      })
      api.ledger(profile.worker_id, addDays(todayIso(), -45), todayIso())
        .then((led) => setDayOptions([...new Set((led.days || []).map((d) => d.date))].sort().reverse()))
        .catch(() => {})
    }
  }

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const e = await api.getEntry(entryId)
        if (!alive) return
        setEntry(e)
        if (e.status === 'confirmed') { init(e, Object.fromEntries(Object.entries(e.confirmed || {}).map(([k, x]) => [k, { value: x, status: 'green' }]))); setPhase('done'); return }
        if (e.status === 'processed') { init(e, e.reconciled?.fields, e.reply); setPhase('ready'); return }
        if (!e.audio_path) { init(e, e.reconciled?.fields, e.reply); setPhase('ready'); return }
        setPhase('processing')
        const r = await api.processEntry(entryId)
        if (!alive) return
        setEntry({ ...e, status: r.status, transcript: r.transcript })
        init(e, r.fields, r.reply)
        if (r.status === 'processed') {
          setPhase('ready')
          if (localId) updateRecord(localId, { status: 'processed' })
        } else { setBlockCode(r.error); setPhase('blocked') }
      } catch (err) {
        if (alive) { setBlockCode(err.code || 'NETWORK'); setPhase('error') }
      }
    })()
    return () => { alive = false }
  }, [entryId])

  const kind = entry?.kind || 'workday'
  const speaker = entry?.speaker || 'worker'
  const rows = kind === 'payment' ? PAYMENT_ROWS
    : kind === 'hisaab_statement' ? (speaker === 'thekedar' ? [INTENT_ROW, ...STATEMENT_ROWS] : STATEMENT_ROWS)
      : kind === 'coworker_confirm' ? COWORKER_ROWS : WORKDAY_ROWS
  const setVal = (name, value) => { setVals((v) => ({ ...v, [name]: value })); setTouched((t) => ({ ...t, [name]: true })) }

  function statusOf(name, required) {
    if (touched[name]) return isEmpty(vals[name]) ? (required ? 'red' : null) : 'green'
    const s = fields[name]?.status
    if (s === 'green' || s === 'amber' || s === 'red') {
      if (s === 'green' && isEmpty(vals[name])) return 'red'
      if (s === 'red' && !required && isEmpty(vals[name]) && (kind === 'hisaab_statement' || kind === 'coworker_confirm')) return null
      return s
    }
    if (required && isEmpty(vals[name])) return 'red'
    if (!isEmpty(vals[name])) return 'amber' // e.g. thekedar filled from the profile
    return null
  }

  async function submitP3() {
    const pick = (names) => Object.fromEntries(names.filter((n) => !isEmpty(vals[n])).map((n) => [n, vals[n]]))
    let body
    if (kind === 'hisaab_statement') {
      if (speaker === 'thekedar' && !vals.intent) { toast('ठेकेदार ने क्या कहा — चुनें'); setSheet('intent'); return }
      const nums = STATEMENT_NUMS.filter((n) => !isEmpty(vals[n]))
      if (!nums.length) { toast('कम से कम एक संख्या भरें — दिन, दर या रक़म'); setSheet('days_counted'); return }
      body = {
        ...Object.fromEntries(nums.map((n) => [n, parseInt(vals[n], 10)])),
        ...pick(['promised_date']),
        ...(speaker === 'thekedar' ? { intent: vals.intent } : {}),
      }
    } else {
      if (isEmpty(vals.dates)) { toast('किन दिनों साथ काम किया — दिन चुनें'); setSheet('dates'); return }
      if (!vals.consent) { toast('साथी ने रिकॉर्डिंग के लिए हाँ कहा — यह पक्का करें'); return }
      body = { ...pick(['coworker_name', 'dates_or_days', 'site', 'consent_phrase']), consent: true, dates: [...vals.dates].sort() }
    }
    setSaving(true)
    try {
      const r = await api.confirmEntry(entryId, body)
      const recs = await getRecords()
      const lid = localId || Object.values(recs).find((x) => x.serverId === entryId)?.localId
      if (lid) await updateRecord(lid, { status: 'confirmed' })
      if (kind === 'hisaab_statement') replace('diff', { entryId })
      else { toast(`गवाही पक्की · रिकॉर्ड कोड ${r.chain_head?.short || ''}`); reset('ledger') }
    } catch (e) {
      setSaving(false)
      toast(e instanceof api.NetworkError ? 'हब से जुड़ने पर पक्का करें — आवाज़ सेव है' : `पक्का नहीं हो पाया (${e.code})`)
    }
  }

  async function submit() {
    if (kind === 'hisaab_statement' || kind === 'coworker_confirm') { submitP3(); return }
    const needed = kind === 'payment' ? ['payment_date', 'amount_paid'] : ['work_date', 'start_time', 'end_time', 'break_minutes']
    const missing = needed.find((n) => vals[n] == null || vals[n] === '')
    if (missing) { toast('लाल वाली बात बताना ज़रूरी है'); setSheet(missing); return }
    const worked = kind === 'workday' ? workedMinutes(vals.start_time, vals.end_time, vals.break_minutes) : null
    if (worked != null && worked > 16 * 60) { toast('काम 16 घंटे से ज़्यादा दिख रहा है — समय जाँचें'); setSheet('end_time'); return }
    const pick = (names) => Object.fromEntries(names.filter((n) => vals[n] != null && vals[n] !== '').map((n) => [n, vals[n]]))
    const body = kind === 'payment'
      ? pick(['payment_date', 'amount_paid', 'payment_mode', 'payer_name', 'covers_from', 'deductions'])
      : { ...pick(['work_date', 'start_time', 'end_time', 'break_minutes', 'contractor_name', 'coworkers_present']), worked: 'yes' }
    setSaving(true)
    try {
      const r = await api.confirmEntry(entryId, body)
      const recs = await getRecords()
      const lid = localId || Object.values(recs).find((x) => x.serverId === entryId)?.localId
      if (lid) await updateRecord(lid, { status: 'confirmed' })
      toast(`पक्का हो गया · रिकॉर्ड कोड ${r.chain_head?.short || ''}`)
      reset('home')
    } catch (e) {
      setSaving(false)
      toast(e instanceof api.NetworkError ? 'हब से जुड़ने पर पक्का करें — आवाज़ सेव है' : `पक्का नहीं हो पाया (${e.code})`)
    }
  }

  const title = {
    payment: 'पैसा मिला — पक्का करें',
    hisaab_statement: speaker === 'thekedar' ? 'ठेकेदार की बात — पक्का करें' : 'हिसाब — पक्का करें',
    coworker_confirm: 'साथी की गवाही — पक्का करें',
  }[kind] || 'पक्का करें'
  const understanding = {
    payment: 'रक़म, तारीख, देने वाला पहचान रहे हैं (1–2 मिनट)',
    hisaab_statement: 'दिन, दर, कटौती, दी गई रक़म पहचान रहे हैं (1–2 मिनट)',
    coworker_confirm: 'साथी का नाम, दिन, साइट पहचान रहे हैं (1–2 मिनट)',
  }[kind] || 'समय, ठेकेदार, साथी पहचान रहे हैं (1–2 मिनट)'
  const saidBy = speaker === 'thekedar' ? 'ठेकेदार ने कहा:' : speaker === 'coworker' ? 'साथी ने कहा:' : 'आपने कहा:'
  if (phase === 'loading' || phase === 'processing') {
    return (
      <div className="screen">
        <TopBar title={title} onBack={back} speakText="समझ रहे हैं, थोड़ा रुकिए" />
        <div className="card steps" style={{ marginTop: 20 }}>
          <div className="row"><Spinner /> <div><div style={{ fontWeight: 700 }}>समझ रहे हैं…</div><div className="small" style={{ color: 'var(--text-2)' }}>{phase === 'processing' ? understanding : 'खोल रहे हैं…'}</div></div></div>
        </div>
      </div>
    )
  }
  if (phase === 'error') {
    return (
      <div className="screen">
        <TopBar title={title} onBack={back} speakText="हब से नहीं जुड़ पाए। आवाज़ सेव है, बाद में पक्का करें।" />
        <div className="info-row" style={{ marginTop: 20 }}><CircleAlert size={22} color="var(--urgent)" /> हब से नहीं जुड़ पाए ({blockCode})। आवाज़ फ़ोन में सेव है — जुड़ने पर पक्का करें।</div>
        <div className="bottom-actions"><Btn variant="plain" onClick={() => reset('home')}>होम पर जाएँ</Btn></div>
      </div>
    )
  }

  const readOnly = phase === 'done'
  const manual = kind === 'hisaab_statement' && !entry?.audio_path && !entry?.transcript
  const mins = kind === 'workday' ? workedMinutes(vals.start_time, vals.end_time, vals.break_minutes) : null
  const ot = mins != null ? Math.max(0, mins - 480) : 0
  const amountField = fields.amount_paid || {}

  return (
    <div className="screen">
      <TopBar title={title} onBack={back} speakText={readbackText(kind, Object.fromEntries(Object.entries(vals).map(([k, v]) => [k, { value: v }])))} />

      <div className="quote">
        <div className="q"><Quote size={16} /> {copied ? 'कल की एंट्री से भरा:' : manual ? 'टाइप करके भरें:' : saidBy}</div>
        <p>{copied ? 'हर बात देखकर पक्का करें — कल जैसा ही था?' : manual ? 'ठेकेदार ने जो बताया, नीचे भरें — जो नहीं पता, ख़ाली छोड़ें।' : entry?.transcript ? `“${entry.transcript}”` : 'आवाज़ में कोई बात साफ़ नहीं सुनाई दी — नीचे खुद भरें।'}</p>
      </div>

      {phase === 'blocked' && (
        <div className="info-row" style={{ marginTop: 12, background: 'var(--ask-bg)', color: 'var(--ask)' }}>
          <CircleAlert size={20} /> हब पर समझने वाला मॉडल अभी बंद है ({blockCode}) — नीचे सिर्फ़ गिनती वाली पढ़ाई है। आवाज़ सेव है, थोड़ी देर बाद पक्का करें।
        </div>
      )}
      {readOnly && <div className="info-row" style={{ marginTop: 12 }}><CircleCheck size={20} color="var(--brand)" /> यह एंट्री पहले ही पक्की हो चुकी है।</div>}
      {readOnly && kind === 'hisaab_statement' && <Btn variant="outline" icon={Scale} style={{ marginTop: 12 }} onClick={() => go('diff', { entryId })}>मिलान देखें</Btn>}

      {kind === 'payment' && (
        <>
          <div className="card amount-card" style={{ marginTop: 12 }}>
            <div className="row between">
              <div>
                <div className="muted" style={{ fontSize: 14 }}>मिली रक़म</div>
                <button className="big" onClick={() => !readOnly && setSheet('amount_paid')}>{vals.amount_paid != null ? rupees(vals.amount_paid) : '₹ —'}</button>
              </div>
              <StatusChip status={statusOf('amount_paid', true)} />
            </div>
            {!touched.amount_paid && amountField.source === 'both' && amountField.span && (
              <div className="both"><CircleCheck size={18} /> “{amountField.span}” = {Number(vals.amount_paid).toLocaleString('en-IN')} · दोनों तरीक़ों से मिला</div>
            )}
            {!touched.amount_paid && amountField.candidates?.length > 1 && (
              <div className="both" style={{ color: 'var(--ask)' }}><CircleHelp size={18} /> दो अलग रक़म सुनी — टैप करके सही चुनें</div>
            )}
          </div>
          <div className="label">कैसे मिला</div>
          <div className="toggle-chips">
            {MODES.map(([v, l]) => (
              <button key={v} className={`tchip ${vals.payment_mode === v ? 'on' : ''}`} style={{ minWidth: 92 }} disabled={readOnly} onClick={() => setVal('payment_mode', v)}>{l}</button>
            ))}
          </div>
        </>
      )}

      <div className="card fields">
        {rows.map((r) => {
          const st = statusOf(r.name, r.required)
          const v = vals[r.name]
          const shown = isEmpty(v) ? null : r.fmt ? r.fmt(v) : String(v)
          const I = r.icon
          return (
            <button key={r.name} className={`frow ${st === 'amber' ? 'ask' : st === 'red' ? 'urgent' : ''}`} onClick={() => !readOnly && setSheet(r.name)}>
              <span className={`icon-bubble ${st === 'amber' || st === 'red' ? 'white' : ''}`}><I size={18} /></span>
              <div className="grow">
                <div className="fl">{r.label}</div>
                <div className={`fv ${shown ? '' : 'muted'}`}>{shown || (fields[r.name]?.candidates?.length > 1 ? 'दो जवाब — चुनें' : r.empty || 'बताना है')}</div>
              </div>
              <StatusChip status={st} />
            </button>
          )
        })}
      </div>

      {kind === 'coworker_confirm' && (
        <div className={`option ${vals.consent ? 'on' : ''}`} style={{ marginTop: 12, ...(vals.consent ? {} : { background: 'var(--urgent-bg)', borderColor: 'var(--urgent)' }) }}
          onClick={() => !readOnly && setVal('consent', !vals.consent)} role="checkbox" aria-checked={!!vals.consent}>
          <span className={`check-box ${vals.consent ? 'on' : ''}`}>{vals.consent && <Check size={15} strokeWidth={3} />}</span>
          <div className="body"><div className="name" style={{ fontSize: 16.5 }}>साथी ने रिकॉर्डिंग के लिए हाँ कहा</div><div className="desc">ज़रूरी — रिकॉर्डिंग में उनकी हाँ सुनकर टिक करें</div></div>
        </div>
      )}

      {kind === 'workday' && mins != null && (
        <div className="sum-pill"><Timer size={20} /> कुल {hoursText(mins)} · {ot ? `${hoursText(ot).replace('घंटे', ot === 60 ? 'घंटा' : 'घंटे')} ओवरटाइम` : 'ओवरटाइम नहीं'}</div>
      )}
      <button className="btn plain" style={{ marginTop: kind === 'workday' ? 0 : 12 }} onClick={() => speak(readbackText(kind, Object.fromEntries(Object.entries(vals).map(([k, v]) => [k, { value: v }]))))}>
        <Volume2 size={22} color="var(--brand)" /> पढ़कर सुनाएँ
      </button>

      {!readOnly && (
        <div className="bottom-actions">
          <div className="btn-row">
            <Btn variant="outline" className="narrow" icon={Pencil} onClick={() => setSheet(rows.find((r) => statusOf(r.name, r.required) !== 'green')?.name || rows[0].name)}>बदलें</Btn>
            <Btn icon={Check} onClick={submit} disabled={saving || phase === 'blocked'}>{saving ? 'सेव…' : 'सही है'}</Btn>
          </div>
          <div className="legend">
            <span style={{ color: 'var(--ok)' }}><i style={{ background: 'var(--brand)' }} /> ✓ ठीक</span>
            <span style={{ color: 'var(--ask)' }}><i style={{ background: 'var(--ask)' }} /> ? पक्का करें</span>
            <span style={{ color: 'var(--urgent)' }}><i style={{ background: 'var(--urgent)' }} /> ! बताना ज़रूरी</span>
          </div>
        </div>
      )}

      <FieldSheet name={sheet} field={sheet ? fields[sheet] : null} value={sheet ? vals[sheet] : null} dayOptions={dayOptions}
        row={[...rows, { name: 'amount_paid', label: 'मिली रक़म', editor: 'amount' }].find((r) => r.name === sheet)}
        onClose={() => setSheet(null)} onPick={(v) => { setVal(sheet, v); setSheet(null) }} />
    </div>
  )
}

// --- editors -------------------------------------------------------------------
const PARTS = [['am', 'सुबह'], ['noon', 'दोपहर'], ['pm', 'शाम'], ['night', 'रात']]
function to24(h, part) {
  if (part === 'am') return h % 12
  if (part === 'noon') return h === 12 ? 12 : h <= 4 ? h + 12 : h
  if (part === 'pm') return h < 12 ? h + 12 : h
  return h >= 8 && h <= 11 ? h + 12 : h === 12 ? 0 : h
}
function from24(hhmm) {
  if (!hhmm) return { h: 9, m: 0, part: 'am' }
  const [H, M] = hhmm.split(':').map(Number)
  const part = H < 12 && H >= 4 ? 'am' : H >= 12 && H < 16 ? 'noon' : H >= 16 && H < 20 ? 'pm' : 'night'
  return { h: H % 12 || 12, m: M, part }
}

// Hour, minute and part of day are kept as separate state: deriving the part back from the 24h value
// after each tap loses it (21:00 reads as रात, so a later tap on 7 would give 07:00).
function TimeEditor({ label, value, onChange }) {
  const [t, setT] = useState(() => from24(value))
  const set = (patch) => {
    const n = { ...t, ...patch }
    setT(n)
    onChange(`${String(to24(n.h, n.part)).padStart(2, '0')}:${String(n.m).padStart(2, '0')}`)
  }
  const shown = `${String(to24(t.h, t.part)).padStart(2, '0')}:${String(t.m).padStart(2, '0')}`
  return (
    <>
      <h2>{label}</h2>
      <div className="toggle-chips" style={{ margin: '10px 0' }}>
        {PARTS.map(([p, l]) => <button key={p} className={`tchip ${t.part === p ? 'on' : ''}`} onClick={() => set({ part: p })}>{l}</button>)}
      </div>
      <div className="picker">
        {Array.from({ length: 12 }, (_, i) => i + 1).map((h) => <button key={h} className={t.h === h ? 'on' : ''} onClick={() => set({ h })}>{h}</button>)}
      </div>
      <div className="picker" style={{ marginTop: 10 }}>
        {[0, 15, 30, 45].map((m) => <button key={m} className={t.m === m ? 'on' : ''} onClick={() => set({ m })}>:{String(m).padStart(2, '0')}</button>)}
      </div>
      <p className="center" style={{ fontWeight: 700, fontSize: 20 }}>{value ? clockLong(shown) : '—'}</p>
    </>
  )
}

function FieldSheet({ name, field, value, row, onClose, onPick, dayOptions = [] }) {
  const [draft, setDraft] = useState(value)
  useEffect(() => { setDraft(value) }, [name, value])
  if (!name || !row) return null
  const cands = field?.candidates?.length > 1 ? field.candidates : []
  const t = todayIso()

  let body = null
  if (row.editor === 'date') {
    const span = field?.span
    const days = [0, 1, 2, 3, 4, 5, 6].map((n) => addDays(t, -n))
    body = (
      <>
        <div className="kicker"><CircleHelp size={20} /> एक सवाल</div>
        <h2>{span ? `आपने कहा “${span}”। कौन-सा दिन?` : 'कौन-सा दिन?'}</h2>
        {span === 'कल' && <p className="muted" style={{ marginTop: 0 }}>हिंदी में ‘कल’ बीता हुआ भी हो सकता है और आने वाला भी।</p>}
        <div className="stack" style={{ marginTop: 12 }}>
          {days.slice(0, 4).map((d, i) => (
            <div key={d} className={`option ${draft === d ? 'on' : ''}`} onClick={() => setDraft(d)} role="radio" aria-checked={draft === d}>
              <div className="body"><div className="name">{['आज', 'बीता हुआ कल', 'परसों (बीता)', 'उससे पहले'][i]}</div><div className="desc">{longDate(d)}</div></div>
              <span className={`radio ${draft === d ? 'on' : ''}`}>{draft === d && <Check size={13} strokeWidth={3} />}</span>
            </div>
          ))}
          <div className="option" style={{ opacity: 0.5 }} aria-disabled>
            <div className="body"><div className="name">आने वाला कल</div><div className="desc">{longDate(addDays(t, 1))} · आगे के दिन का काम दर्ज नहीं होता</div></div>
            <span className="radio" />
          </div>
        </div>
      </>
    )
  } else if (row.editor === 'time') {
    body = <TimeEditor key={name} label={row.label} value={draft} onChange={setDraft} />
  } else if (row.editor === 'break') {
    body = (
      <>
        <h2>{row.label}</h2>
        <div className="stack" style={{ marginTop: 10 }}>
          {[0, 30, 45, 60, 90].map((m) => (
            <div key={m} className={`option ${Number(draft) === m && draft !== null ? 'on' : ''}`} onClick={() => setDraft(m)} role="radio">
              <div className="body"><div className="name">{breakText(m)}</div></div>
              <span className={`radio ${Number(draft) === m && draft !== null ? 'on' : ''}`}>{Number(draft) === m && draft !== null && <Check size={13} strokeWidth={3} />}</span>
            </div>
          ))}
        </div>
      </>
    )
  } else if (row.editor === 'number') {
    body = (
      <>
        <h2>{row.label}</h2>
        <div className="field" style={{ marginTop: 10 }}>
          <input inputMode="numeric" autoFocus value={draft ?? ''} onChange={(e) => { const d = e.target.value.replace(/\D/g, '').slice(0, 3); setDraft(d ? Number(d) : null) }} />
          <span style={{ fontWeight: 700 }}>दिन</span>
        </div>
      </>
    )
  } else if (row.editor === 'intent') {
    body = (
      <>
        <h2>{row.label}?</h2>
        <div className="stack" style={{ marginTop: 10 }}>
          {INTENTS.map(([k, l]) => (
            <div key={k} className={`option ${draft === k ? 'on' : ''}`} onClick={() => setDraft(k)} role="radio" aria-checked={draft === k}>
              <div className="body"><div className="name">{l}</div></div>
              <span className={`radio ${draft === k ? 'on' : ''}`}>{draft === k && <Check size={13} strokeWidth={3} />}</span>
            </div>
          ))}
        </div>
      </>
    )
  } else if (row.editor === 'dates') {
    const cur = Array.isArray(draft) ? draft : []
    const opts = [...new Set([...cur, ...dayOptions])].sort().reverse()
    const flip = (d) => setDraft(cur.includes(d) ? cur.filter((x) => x !== d) : [...cur, d])
    body = (
      <>
        <h2>{row.label}?</h2>
        <p className="muted" style={{ marginTop: 0 }}>आपके पक्के काम के दिन</p>
        <div className="stack" style={{ marginTop: 8 }}>
          {opts.length === 0 && <div className="info-row">हब से जुड़ने पर आपके पक्के दिन यहाँ दिखेंगे</div>}
          {opts.map((d) => (
            <div key={d} className={`option ${cur.includes(d) ? 'on' : ''}`} style={{ minHeight: 52 }} onClick={() => flip(d)} role="checkbox" aria-checked={cur.includes(d)}>
              <div className="body"><div className="name">{longDate(d)}</div></div>
              <span className={`check-box ${cur.includes(d) ? 'on' : ''}`}>{cur.includes(d) && <Check size={15} strokeWidth={3} />}</span>
            </div>
          ))}
        </div>
      </>
    )
  } else if (row.editor === 'amount') {
    body = (
      <>
        <h2>{row.label}</h2>
        <div className="field" style={{ marginTop: 10 }}>
          <span style={{ fontWeight: 700, fontSize: 20 }}>₹</span>
          <input inputMode="numeric" autoFocus value={draft ?? ''} onChange={(e) => setDraft(e.target.value.replace(/\D/g, '').slice(0, 6) ? Number(e.target.value.replace(/\D/g, '').slice(0, 6)) : null)} />
        </div>
      </>
    )
  } else {
    body = (
      <>
        <h2>{row.label}</h2>
        <div className="field" style={{ marginTop: 10 }}>
          <input autoFocus value={draft ?? ''} onChange={(e) => setDraft(e.target.value)} maxLength={80} />
        </div>
      </>
    )
  }

  return (
    <Sheet open onClose={onClose}>
      {cands.length > 1 && (
        <div className="card ask" style={{ padding: 12, marginBottom: 12 }}>
          <div style={{ fontWeight: 700, color: 'var(--ask)' }}>दो जवाब मिले — सही चुनें</div>
          <div className="toggle-chips" style={{ marginTop: 8 }}>
            {cands.map((c) => (
              <button key={String(c)} className={`tchip ${draft === c ? 'on' : ''}`} onClick={() => setDraft(c)}>
                {row.editor === 'time' ? clockLong(c) : row.editor === 'date' ? dayMonth(c) : row.editor === 'amount' ? rupees(c) : String(c)}
              </button>
            ))}
          </div>
        </div>
      )}
      {body}
      <div className="btn-row" style={{ marginTop: 16 }}>
        <Btn variant="plain" className="narrow" onClick={() => onPick(null)}>पता नहीं</Btn>
        <Btn icon={Check} onClick={() => onPick(draft === '' ? null : draft)}>यही सही है</Btn>
      </div>
    </Sheet>
  )
}

