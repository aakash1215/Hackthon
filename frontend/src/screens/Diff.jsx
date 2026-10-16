// मिलान (UI/ H4): what the thekedar said vs. what the worker's own record gives. Every number comes
// from the hub (/differences, wage engine); the phone only formats them into fixed templates.
// "भेजें" first shows the risk notice from UI/ S3 (composed as a sheet), then Web Share.
import { useEffect, useState } from 'react'
import { ChevronRight, CircleAlert, CircleCheck, Play, Send, TriangleAlert, Users, HardHat, Volume2 } from 'lucide-react'
import { Btn, Sheet, Spinner, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { speak } from '../lib/device.js'
import { rupees } from '../lib/format.js'

const n = (v) => (v == null || v === '' ? null : Number(v))
const absRupees = (v) => rupees(Math.abs(n(v)))

/** Display spec per difference code: label, the two cells, the detail line and the action. */
function view(it) {
  const diff = n(it.diff)
  switch (it.code) {
    case 'DAYS_DIFF': {
      const fewer = n(it.thekedar) != null && n(it.record) != null ? n(it.thekedar) < n(it.record) : true
      // it.dates are all recorded days, not the missing ones: which day he dropped is unknown, so never name one.
      const detail = `${Math.abs(diff ?? 0)} दिन ${fewer ? 'कम' : 'ज़्यादा'} गिने`
      return { label: 'काम के दिन', a: it.thekedar ?? '—', b: it.record ?? '—', detail, act: 'proof' }
    }
    case 'RATE_BELOW_MIN':
      return { label: 'रोज़ की दर', a: rupees(it.thekedar), b: rupees(it.record), detail: `कानूनी न्यूनतम से ${absRupees(it.diff)} कम`, act: 'why' }
    case 'OT_NOT_COUNTED':
      return { label: 'ओवरटाइम', a: rupees(it.thekedar ?? 0), b: `${n(it.record) ?? '—'} घंटे`, detail: 'दोगुनी दर से बनता है', act: 'proof' }
    case 'DEDUCTION_DISPUTED':
      return {
        label: 'उचल कटौती', a: `− ${absRupees(it.thekedar)}`, b: n(it.record) ? `− ${absRupees(it.record)}` : 'नहीं',
        detail: n(it.record) ? 'आपके रिकॉर्ड से अलग' : 'आपके रिकॉर्ड में उचल नहीं', act: 'ask',
      }
    case 'PAID_DIFF':
      return { label: 'कितना दिया', a: rupees(it.thekedar), b: rupees(it.record), detail: diff != null ? `${absRupees(diff)} का फ़र्क़` : 'रक़म अलग', act: 'proof' }
    default:
      return { label: it.code, a: String(it.thekedar ?? '—'), b: String(it.record ?? '—'), detail: '', act: null }
  }
}

/** Fixed-template sentences (spoken by "समझाइए", shared by "भेजें"). */
function sentence(it) {
  const v = view(it)
  switch (it.code) {
    case 'DAYS_DIFF': return `काम के दिन: ठेकेदार ने ${v.a} गिने, आपके रिकॉर्ड में ${v.b} हैं।`
    case 'RATE_BELOW_MIN': return `रोज़ की दर: ठेकेदार ${v.a}, सरकारी न्यूनतम ${v.b}।`
    case 'OT_NOT_COUNTED': return `ओवरटाइम: आपके रिकॉर्ड में ${v.b} हैं, ठेकेदार के हिसाब में ${v.a}। यह दोगुनी दर से बनता है।`
    case 'DEDUCTION_DISPUTED': return `उचल कटौती: ठेकेदार ने ${absRupees(it.thekedar)} काटे, आपके रिकॉर्ड में ${v.b === 'नहीं' ? 'उचल नहीं है' : v.b}।`
    case 'PAID_DIFF': return `कितना दिया: ठेकेदार ${v.a}, आपके रिकॉर्ड में ${v.b}।`
    default: return `${v.label}: ठेकेदार ${v.a}, आपका रिकॉर्ड ${v.b}।`
  }
}

export default function Diff({ entryId }) {
  const { back, go, toast } = useApp()
  const [d, setD] = useState(null)
  const [err, setErr] = useState(null)
  const [sendOpen, setSendOpen] = useState(false)

  useEffect(() => {
    api.differences(entryId).then(setD).catch((e) => setErr(e.code || 'NETWORK'))
  }, [entryId])

  if (err || !d) {
    return (
      <div className="screen">
        <TopBar title="मिलान" onBack={back} speakText="मिलान" />
        {err
          ? <div className="info-row" style={{ marginTop: 16 }}><CircleAlert size={22} color="var(--urgent)" /> मिलान नहीं खुल पाया ({err}) — हब से जुड़ने पर फिर देखें।</div>
          : <div className="row" style={{ marginTop: 20 }}><Spinner /> मिलान कर रहे हैं…</div>}
      </div>
    )
  }

  const items = d.items || []
  const notif = String(d.provenance?.notification_no || '').slice(-4)
  const summary = [
    `ठेकेदार का हिसाब: ${rupees(d.thekedar_total)}।`,
    `आपके रिकॉर्ड से बनता: ${rupees(d.record_total)}।`,
    items.length ? `${items.length} फ़र्क़ मिले।` : 'कोई फ़र्क़ नहीं मिला।',
    ...items.map(sentence),
    'सब रक़म अनुमान हैं।',
  ]
  const shareText = `अपना हिसाब — मिलान\n${summary.join('\n')}`

  async function share() {
    setSendOpen(false)
    try {
      if (navigator.share) { await navigator.share({ title: 'अपना हिसाब — मिलान', text: shareText }); return }
    } catch (e) {
      if (e?.name === 'AbortError') return
    }
    try {
      await navigator.clipboard.writeText(shareText)
      toast('संदेश कॉपी हो गया — जहाँ भेजना हो वहाँ चिपकाएँ')
    } catch {
      toast('शेयर नहीं हो पाया')
    }
  }

  const act = (v) => {
    if (v.act === 'proof') return <button className="pill-act" onClick={() => go('ledger')}><Play size={16} fill="currentColor" /> सबूत</button>
    if (v.act === 'why') return <button className="pill-act" onClick={() => go('hisaab')}>क्यों?</button>
    if (v.act === 'ask') return <button className="pill-act" onClick={() => go('recordOther', { who: 'thekedar' })}>पूछें</button>
    return null
  }

  return (
    <div className="screen">
      <TopBar title="मिलान" onBack={back} speakText={summary.join(' ')} />
      <div className="card diff-top">
        <div><div className="k">ठेकेदार का हिसाब</div><div className="v">{rupees(d.thekedar_total)}</div></div>
        <div><div className="k">आपके रिकॉर्ड से बनता</div><div className="v blue">{rupees(d.record_total)}</div></div>
      </div>

      {items.length === 0 ? (
        <>
          <div style={{ marginTop: 14 }}><span className="chip ok"><CircleCheck size={18} /> कोई फ़र्क़ नहीं मिला</span></div>
          <div className="info-row" style={{ marginTop: 12 }}><CircleCheck size={20} color="var(--brand)" /> ठेकेदार का हिसाब आपके रिकॉर्ड से मेल खाता है।</div>
        </>
      ) : (
        <>
          <div style={{ marginTop: 14 }}><span className="chip urgent"><CircleAlert size={18} /> {items.length} फ़र्क़ मिले</span></div>
          <div className="diff-cols"><span /><span>ठेकेदार</span><span>आपका रिकॉर्ड</span></div>
          {items.map((it, i) => {
            const v = view(it)
            return (
              <div key={`${it.code}${i}`} className={`diff-item ${it.severity === 'ask' ? 'ask' : ''}`}>
                <div className="top"><span className="l">{v.label}</span><span className="a">{v.a}</span><span className="b">{v.b}</span></div>
                <div className="bot"><span className="d">{v.detail}</span>{act(v)}</div>
              </div>
            )
          })}
        </>
      )}

      <div className="diff-actions" style={{ marginTop: 'auto', paddingTop: 12 }}>
        <Btn icon={Volume2} onClick={() => speak(summary.join(' '))}>समझाइए</Btn>
        <Btn variant="outline" icon={Send} onClick={() => { setSendOpen(true); speak('भेजने से ठेकेदार को पता चलेगा कि आप अपना हिसाब रखते हैं। पहले यूनियन या सहायक को भेजना ज़्यादा सुरक्षित हो सकता है।') }}>भेजें</Btn>
        <Btn variant="outline" onClick={() => go('recordOther', { who: 'thekedar' })}>बोल के बताओ</Btn>
      </div>
      <div className="foot">सब रक़म अनुमान हैं{notif ? ` — दरें सरकारी अधिसूचना ${notif} से` : ''}</div>

      <Sheet open={sendOpen} onClose={() => setSendOpen(false)}>
        <h2 style={{ textAlign: 'center' }}>क्या यह ठेकेदार को भेजना है?</h2>
        <div className="card ask notice-card" style={{ marginTop: 10 }}>
          <div className="h"><TriangleAlert size={18} /> भेजने से पहले सुनें</div>
          <p style={{ margin: '6px 0 0', fontSize: 15.5 }}>भेजने से ठेकेदार को पता चलेगा कि आप अपना हिसाब रखते हैं। पहले यूनियन या सहायक को भेजना ज़्यादा सुरक्षित हो सकता है।</p>
        </div>
        <div className="stack" style={{ marginTop: 12 }}>
          <button className="option on" onClick={share}>
            <span className="avatar brand"><Users size={22} /></span>
            <div className="body"><div className="name">यूनियन / सहायक को भेजें</div><span className="chip ok sm">ज़्यादा सुरक्षित</span></div>
            <ChevronRight size={22} color="var(--text-2)" />
          </button>
          <button className="option" onClick={share}>
            <span className="avatar"><HardHat size={22} /></span>
            <div className="body"><div className="name">ठेकेदार को भेजें</div><div className="desc">सिर्फ़ तथ्य, विनम्र भाषा में</div></div>
            <ChevronRight size={22} color="var(--text-2)" />
          </button>
          <Btn variant="plain" onClick={() => setSendOpen(false)}>अभी नहीं</Btn>
        </div>
      </Sheet>
    </div>
  )
}
