// Home (UI/ D1). Additions in the same style: upload-queue status in the trust chip and a
// "phone-saved / to confirm" list (BUILD_PLAN P2 offline queue).
import { useEffect, useState } from 'react'
import { Banknote, Check, ChevronRight, CircleAlert, CloudUpload, History, Mic, Scale, ShieldAlert, ShieldCheck } from 'lucide-react'
import { TabBar, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { read, write } from '../lib/db.js'
import { clock12, localIso, longDate, monthRange, rupees, todayIso, weekOf, weekdayShort } from '../lib/format.js'
import { shortCode } from '../lib/hash.js'
import { pendingRecords } from '../lib/sync.js'

const KIND_LABEL = { workday: 'काम', payment: 'पैसा मिला', hisaab_statement: 'हिसाब', thekedar: 'ठेकेदार की बात', coworker_confirm: 'साथी की गवाही' }

export default function Home() {
  const { profile, sync, go, toast } = useApp()
  const [data, setData] = useState(null)
  const [pending, setPending] = useState([])
  const [copying, setCopying] = useState(false)
  const today = todayIso()
  const name = profile.display_name || 'साथी'

  useEffect(() => {
    let alive = true
    read('cache:home').then((c) => { if (alive && c) setData(c) })
    const d = new Date()
    const [from] = monthRange(d.getFullYear(), d.getMonth())
    const week = weekOf(today)
    Promise.all([
      api.ledger(profile.worker_id, week[0] < from ? week[0] : from, today),
      api.hisaab(profile.worker_id, from, today),
    ]).then(([led, his]) => {
      const fresh = { led, his, at: Date.now() }
      if (alive) setData(fresh)
      write('cache:home', fresh)
    }).catch(() => {})
    return () => { alive = false }
  }, [profile.worker_id, today, sync.hub])

  useEffect(() => { pendingRecords().then(setPending) }, [sync.queued, sync.running])

  const days = data?.led?.days || []
  const pays = data?.led?.payments || []
  const doneDays = new Set(days.map((x) => x.date))
  const last = [...days].filter((x) => x.date < today).sort((a, b) => (a.date < b.date ? -1 : 1)).pop()
  const sameLabel = last ? `(${clock12(last.start_time).replace(':00', '')} से ${clock12(last.end_time).replace(':00', '')}${profile.site?.name ? `, ${profile.site.name}` : ''})` : ''

  async function copyYesterday() {
    if (!last) { toast('पहले एक दिन का काम बोलकर पक्का करें'); return }
    setCopying(true)
    try {
      const r = await api.copyYesterday(profile.worker_id, localIso())
      go('confirm', { entryId: r.entry_id, copied: true })
    } catch (e) {
      toast(e instanceof api.NetworkError ? 'हब से जुड़ने पर ही — अभी बोलकर दर्ज करें' : `नहीं हो पाया (${e.code})`)
    } finally {
      setCopying(false)
    }
  }

  const his = data?.his
  const queued = sync.queued || 0
  const offline = !sync.online || sync.hub === false

  return (
    <div className="screen with-tabs">
      <TopBar speakText={`नमस्ते ${name}। आज का काम बोलने के लिए माइक दबाएँ।`} right={
        <div className="hello" style={{ margin: 0, flex: 1 }}>
          <span className="avatar brand">{name.slice(0, 1)}</span>
          <div>
            <div className="name">नमस्ते, {name}</div>
            <div className="date">{longDate(today)}</div>
          </div>
        </div>
      } />
      <div>
        <span className="chip trust">
          <ShieldCheck size={20} />
          {offline ? 'ऑफ़लाइन · सब फ़ोन में सुरक्षित' : 'हब से जुड़ा · सब सुरक्षित'}
          {queued > 0 && ` · ${queued} भेजना बाकी`}
        </span>
      </div>

      <div className="mic-card">
        <div className="h">आज का काम बोलें</div>
        <div className="s">कब से कब तक · ठेकेदार · कौन साथ था</div>
        <button className="mic-btn" onClick={() => go('record', { kind: 'workday' })} aria-label="रिकॉर्ड शुरू करें">
          <span><Mic size={38} /></span>
        </button>
        <div className="press">दबाएँ और बोलें</div>
      </div>

      <button className="same-btn" onClick={copyYesterday} disabled={copying}>
        <History size={24} /> कल जैसा ही {sameLabel}
      </button>

      <div className="action-pair">
        <button className="action-card" onClick={() => go('record', { kind: 'payment' })}>
          <span className="icon-bubble cream"><Banknote size={20} /></span> पैसा मिला
        </button>
        <button className="action-card" onClick={() => go('hisaabCheck')}>
          <span className="icon-bubble blue"><Scale size={20} /></span> हिसाब जाँचें
        </button>
      </div>

      <button className="same-btn" onClick={() => go('recordOther', { who: 'thekedar' })}>
        <ShieldAlert size={24} /> ठेकेदार की बात रिकॉर्ड करें
      </button>

      {pending.length > 0 && (
        <div className="card pending">
          <div style={{ fontWeight: 700, color: 'var(--text-2)', fontSize: 14 }}>पक्का करना बाकी</div>
          {pending.slice(0, 5).map((r) => (
            <button key={r.localId} className="item" onClick={() => (r.serverId ? go('confirm', { entryId: r.serverId, localId: r.localId }) : go('saved', { localId: r.localId }))}>
              <span className="icon-bubble">{r.status === 'queued' ? <CloudUpload size={18} /> : r.status === 'hash_mismatch' || r.status === 'failed' ? <CircleAlert size={18} color="var(--urgent)" /> : <Mic size={18} />}</span>
              <div className="grow">
                <div style={{ fontWeight: 700 }}>{KIND_LABEL[r.speaker === 'thekedar' ? 'thekedar' : r.kind] || 'काम'} · {longDate(r.createdAt.slice(0, 10))}</div>
                <div className="small" style={{ color: 'var(--text-2)' }}>
                  #{shortCode(r.sha256, 2)} · {{ queued: 'फ़ोन में सेव · भेजना बाकी', saved: 'हब पर · पक्का करें', processed: 'पक्का करें', hash_mismatch: 'कोड मेल नहीं खाया', failed: 'नहीं भेजा जा सका' }[r.status] || r.status}
                </div>
              </div>
              <ChevronRight size={20} color="var(--text-2)" />
            </button>
          ))}
        </div>
      )}

      <div className="card week" style={{ marginTop: 12 }}>
        <div className="h">इस हफ़्ते</div>
        <div className="week-days">
          {weekOf(today).map((iso) => (
            <div key={iso}>
              <div className="wd">{weekdayShort(iso)}</div>
              <div className={`dayc ${doneDays.has(iso) ? 'done' : ''} ${iso === today && !doneDays.has(iso) ? 'today' : ''}`}>
                {doneDays.has(iso) ? <Check size={18} /> : Number(iso.slice(8))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <button className="card month-card" onClick={() => go('hisaab')}>
        <div className="grow">
          <div className="h">इस महीने का हिसाब</div>
          {his?.ok ? (
            <>
              <div className="amt">{rupees(his.totals.claim_estimate)} बाकी <span className="chip estimate">अनुमान</span></div>
              <div className="sub">{his.days.length} दिन काम · {rupees(his.totals.paid_total)} मिला</div>
            </>
          ) : (
            <div className="sub" style={{ marginTop: 4 }}>{data ? 'अभी कोई पक्का दिन नहीं' : 'हब से जुड़ने पर दिखेगा'}{pays.length ? ` · ${pays.length} बार पैसा` : ''}</div>
          )}
        </div>
        <ChevronRight size={24} color="var(--text-2)" />
      </button>

      <TabBar active="home" />
    </div>
  )
}
