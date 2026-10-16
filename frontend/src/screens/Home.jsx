// Home (UI/ D1). Additions in the same style: upload-queue status in the trust chip and a
// "phone-saved / to confirm" list (BUILD_PLAN P2 offline queue).
import { useCallback, useEffect, useState } from 'react'
import { Banknote, Check, ChevronRight, CircleAlert, CloudUpload, Handshake, History, MessageCircle, Mic, Scale, ShieldAlert, ShieldCheck } from 'lucide-react'
import { Btn, TabBar, TopBar, useApp } from '../components/Ui.jsx'
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
  const tName = profile.thekedar?.name ? `${profile.thekedar.name} जी` : 'ठेकेदार'

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

  // P4: what the thekedar said on Telegram. Polled while Home is open; errors are ignored (hub/bot down).
  const [inbox, setInbox] = useState([])
  const [acting, setActing] = useState(null)
  const loadInbox = useCallback(() => {
    api.inbox(profile.worker_id).then((r) => setInbox((r.items || []).filter((it) => it.status === 'new'))).catch(() => {})
  }, [profile.worker_id])
  useEffect(() => {
    loadInbox()
    const t = setInterval(loadInbox, 20000)
    return () => clearInterval(t)
  }, [loadInbox])
  async function act(it, action, msg) {
    setActing(it.id)
    try {
      const r = await api.inboxAction(it.id, { action })
      setInbox((xs) => xs.filter((x) => x.id !== it.id))
      if (msg) toast(`${msg}${r.chain_head?.short ? ` · कोड ${r.chain_head.short}` : ''}`)
    } catch (e) {
      toast(e instanceof api.NetworkError ? 'हब से नहीं जुड़ पाए' : `नहीं हो पाया (${e.code})`)
    } finally {
      setActing(null)
    }
  }

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

      <div className="card" style={{ marginTop: 12 }}>
        <button className="settings-row" onClick={() => go('telegram')}>
          <span className="icon-bubble blue"><MessageCircle size={20} /></span>
          <div className="grow"><div className="t">ठेकेदार से Telegram</div><div className="d">सिर्फ़ तय संदेश · हर संदेश सेव</div></div>
          <ChevronRight size={22} color="var(--text-2)" />
        </button>
      </div>

      {inbox.map((it) => <InboxCard key={it.id} it={it} tName={tName} busy={acting === it.id} act={act} go={go} />)}

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

// One Telegram inbox item (BUILD_PLAN §7). The thekedar's words are shown verbatim; nothing is saved
// as a fact until the worker taps a button here or confirms on the वादा screen.
function InboxCard({ it, tName, busy, act, go }) {
  const said = it.text ? <p className="said">“{it.text}”</p> : null
  if (it.kind === 'promise') {
    return (
      <button className="card inbox-card" onClick={() => go('promise', { item: it })}>
        <div className="h"><Handshake size={22} /><span className="grow">{tName} ने वादा किया: {it.amount != null ? rupees(it.amount) : 'रक़म नहीं बताई'}{it.date_text ? ` · ${it.date_text}` : ''}</span><span className="chip blue sm">देखें</span></div>
      </button>
    )
  }
  if (it.kind === 'partial_payment') {
    return (
      <div className="card inbox-card">
        <div className="h"><Banknote size={22} /><span>{tName} कहते हैं {it.amount != null ? rupees(it.amount) : 'पैसे'} दिए। सही है?</span></div>
        {said}
        <div className="btn-row">
          <Btn variant="plain" disabled={busy} onClick={() => act(it, 'deny', 'सेव हुआ: नहीं मिले')}>नहीं मिले</Btn>
          <Btn icon={Check} disabled={busy} onClick={() => act(it, 'confirm', 'सेव हुआ: मिले थे')}>हाँ, मिले थे</Btn>
        </div>
      </div>
    )
  }
  if (it.kind === 'dispute') {
    return (
      <div className="card inbox-card ask">
        <div className="h"><CircleAlert size={22} /><span>{tName} ने दिन नहीं माने</span></div>
        {said}
        <div className="btn-row">
          <Btn variant="plain" disabled={busy} onClick={() => act(it, 'dismiss', 'ठीक है — हटा दिया')}>गलत समझा</Btn>
          <Btn disabled={busy} onClick={() => act(it, 'seen')}>ठीक</Btn>
        </div>
      </div>
    )
  }
  if (it.kind === 'hostile') {
    return (
      <button className="card inbox-card urgent" onClick={() => go('stopped', { item: it })}>
        <div className="h"><ShieldAlert size={22} /><span className="grow">बातचीत रोक दी गई</span><ChevronRight size={22} color="var(--urgent)" /></div>
        <p className="said">आप सुरक्षित रहें — मदद के नंबर देखें</p>
      </button>
    )
  }
  // refuses, or an unclear message
  return (
    <div className={`card inbox-card ${it.kind === 'refuses' ? 'ask' : ''}`}>
      <div className="h">{it.kind === 'refuses' ? <CircleAlert size={22} /> : <MessageCircle size={22} />}<span>{it.kind === 'refuses' ? `${tName} ने मना किया` : `${tName} का नया संदेश`}</span></div>
      {said}
      <div className="btn-row"><Btn variant="plain" disabled={busy} onClick={() => act(it, 'seen')}>ठीक</Btn></div>
    </div>
  )
}
