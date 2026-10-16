// ठेकेदार से Telegram (BUILD_PLAN §7). No UI/ screen exists for this: composed from F2 (status card,
// settings rows, .switch), S4 (WhatsApp button, message preview) and S3 (risk notice before sending).
// The phone never writes text to the thekedar: it only asks the hub to send a fixed template.
import { useCallback, useEffect, useState } from 'react'
import { CircleAlert, FileText, Lock, MessageCircle, Send, Share2, ShieldCheck, TriangleAlert } from 'lucide-react'
import { Btn, Sheet, Spinner, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { tgTime } from '../lib/format.js'

const LANG = { hi: 'हिंदी', mr: 'मराठी', en: 'English' }
const INTENT = {
  promise: ['वादा', 'ok'],
  partial_payment: ['पैसा दिया', 'ok'],
  dispute: ['दिन नहीं माने', 'ask'],
  refuses: ['मना किया', 'ask'],
  hostile: ['बातचीत रोकी', 'urgent'],
}
const TEMPLATES = {
  SUMMARY: { label: 'हिसाब का सारांश भेजें', icon: Send },
  REQUEST_WRITTEN_HISAAB: { label: 'लिखित हिसाब माँगें', icon: FileText },
}
const SEND_ERR = {
  NOT_LINKED: 'ठेकेदार अभी जुड़े नहीं हैं',
  PAUSED: 'बातचीत रुकी है — पहले फिर चालू करें',
  DAILY_LIMIT: 'आज के 5 संदेश हो गए — कल फिर भेजें',
  TELEGRAM_NOT_CONFIGURED: 'Telegram बॉट अभी चालू नहीं',
}
const errText = (e) => (e instanceof api.NetworkError ? 'हब से नहीं जुड़ पाए' : SEND_ERR[e?.code] || `नहीं हो पाया (${e?.code || 'ERROR'})`)

export default function Telegram() {
  const { profile, back, toast } = useApp()
  const wid = profile.worker_id
  const tName = profile.thekedar?.name ? `${profile.thekedar.name} जी` : 'ठेकेदार'
  const [st, setSt] = useState(null) // status response
  const [err, setErr] = useState(null)
  const [msgs, setMsgs] = useState([])
  const [invite, setInvite] = useState(null)
  const [busy, setBusy] = useState(null)
  const [ask, setAsk] = useState(null) // template awaiting the S3 notice
  const [sent, setSent] = useState(null) // text the hub queued

  const load = useCallback(async () => {
    try {
      const s = await api.telegramStatus(wid)
      setSt(s)
      setErr(null)
      if (s.link?.linked) {
        const m = await api.telegramMessages(wid)
        setMsgs(m.items || [])
      }
    } catch (e) {
      setErr(e instanceof api.NetworkError ? 'NETWORK' : e.code)
    }
  }, [wid])

  useEffect(() => {
    load()
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [load])

  async function makeInvite() {
    setBusy('invite')
    try {
      setInvite(await api.telegramInvite(wid))
    } catch (e) {
      toast(errText(e))
    } finally {
      setBusy(null)
    }
  }

  async function share() {
    const text = invite?.share_text || ''
    try {
      if (navigator.share) { await navigator.share({ text }); return }
    } catch (e) {
      if (e?.name === 'AbortError') return
    }
    try {
      await navigator.clipboard.writeText(text)
      toast('लिंक कॉपी हो गया')
    } catch {
      toast('शेयर नहीं हो पाया — लिंक लंबा दबाकर कॉपी करें')
    }
  }

  async function setSetting(patch) {
    setBusy('settings')
    try {
      const link = await api.telegramSettings(wid, patch)
      setSt((s) => ({ ...s, link: { ...s?.link, ...link } }))
    } catch (e) {
      toast(errText(e))
    } finally {
      setBusy(null)
    }
  }

  async function send(template) {
    setAsk(null)
    setBusy(template)
    try {
      const r = await api.telegramSend(wid, template)
      setSent(r.text || '')
      load()
    } catch (e) {
      toast(errText(e))
    } finally {
      setBusy(null)
    }
  }

  const link = st?.link
  const linked = !!link?.linked

  return (
    <div className="screen">
      <TopBar title="ठेकेदार से Telegram" onBack={back} speakText="ठेकेदार से Telegram। ऐप सिर्फ़ तय संदेश भेजता है, और हर संदेश सेव होता है।" />

      {!st && !err && <div className="row" style={{ marginTop: 20 }}><Spinner /> हब से पूछ रहे हैं…</div>}
      {!st && err && (
        <div className="info-row" style={{ marginTop: 12 }}><CircleAlert size={20} color="var(--urgent)" /> हब से नहीं जुड़ पाए ({err}) — थोड़ी देर बाद फिर देखेंगे।</div>
      )}

      {st && !st.configured && (
        <div className="info-row" style={{ marginTop: 12 }}><CircleAlert size={20} color="var(--ask)" /> Telegram बॉट अभी चालू नहीं</div>
      )}

      {st?.configured && !linked && (
        <>
          <div className="card pad stack" style={{ marginTop: 8 }}>
            <div className="row" style={{ alignItems: 'flex-start' }}>
              <span className="icon-bubble blue"><MessageCircle size={20} /></span>
              <div className="grow" style={{ fontSize: 15.5 }}>
                बॉट {tName} को अपना परिचय देगा और बताएगा कि बातचीत रिकॉर्ड होती है।
                <div className="muted" style={{ marginTop: 6, fontSize: 14.5 }}>वह सिर्फ़ तय, सीधे तथ्य भेजता है — कोई बहस या मोल-भाव नहीं। (WhatsApp की जगह Telegram)</div>
              </div>
            </div>
          </div>
          {!st.running && <div className="info-row" style={{ marginTop: 10 }}><CircleAlert size={20} color="var(--ask)" /> बॉट अभी बंद है — लिंक बन सकता है, जुड़ना बाद में होगा</div>}
          {!invite && (
            <Btn className="big" icon={busy === 'invite' ? null : Send} onClick={makeInvite} disabled={busy === 'invite'}>
              {busy === 'invite' ? <><Spinner /> बन रहा है…</> : 'जोड़ने का लिंक बनाएँ'}
            </Btn>
          )}
          {invite && (
            <>
              <div className="card qr-card">
                {invite.qr_png && <img src={invite.qr_png} alt="जोड़ने का QR कोड" />}
                <div className="link-text">{invite.invite_url}</div>
                <div className="small" style={{ marginTop: 8 }}>{tName} यह QR स्कैन करें या लिंक खोलें</div>
              </div>
              <div className="stack" style={{ marginTop: 12 }}>
                <a className="btn whatsapp big" style={{ marginTop: 0 }} href={`https://wa.me/?text=${encodeURIComponent(invite.share_text || invite.invite_url)}`} target="_blank" rel="noopener noreferrer">
                  <MessageCircle size={24} /> WhatsApp पर भेजें
                </a>
                <Btn variant="outline" icon={Share2} onClick={share}>शेयर करें</Btn>
              </div>
              <div className="row small" style={{ justifyContent: 'center', marginTop: 12 }}><Spinner /> जुड़ने का इंतज़ार…</div>
            </>
          )}
        </>
      )}

      {st?.configured && linked && (
        <>
          <div className="status-card">
            <ShieldCheck size={40} />
            <div className="grow">
              <div className="t">{tName} जुड़े हैं</div>
              <div className="muted">{[link.tg_username ? `@${link.tg_username}` : null, LANG[link.lang] || link.lang].filter(Boolean).join(' · ')}</div>
            </div>
          </div>
          {!st.running && <div className="info-row" style={{ marginTop: 10 }}><CircleAlert size={20} color="var(--ask)" /> बॉट अभी बंद है — संदेश बाद में जाएँगे</div>}

          <div className="card opts">
            <div className="orow">
              <span>रोज़ का अपडेट अपने-आप भेजें</span>
              <button className={`switch ${link.auto_daily ? 'on' : ''}`} role="switch" aria-checked={!!link.auto_daily} aria-label="रोज़ का अपडेट अपने-आप भेजें"
                disabled={busy === 'settings' || link.paused} onClick={() => setSetting({ auto_daily: !link.auto_daily })} />
            </div>
          </div>

          {link.paused && (
            <div className="info-row" style={{ marginTop: 12, background: 'var(--urgent-bg)', color: 'var(--urgent)', alignItems: 'center' }}>
              <CircleAlert size={20} />
              <div className="grow" style={{ fontWeight: 700 }}>बातचीत रोकी गई — अपने-आप संदेश बंद</div>
              <button className="pill-act" onClick={() => setSetting({ paused: false })} disabled={busy === 'settings'}>फिर चालू करें</button>
            </div>
          )}

          <div className="stack" style={{ marginTop: 12 }}>
            {Object.entries(TEMPLATES).map(([id, t]) => (
              <Btn key={id} variant="outline" icon={busy === id ? null : t.icon} disabled={!!busy || link.paused} onClick={() => setAsk(id)}>
                {busy === id ? <><Spinner /> भेज रहे हैं…</> : t.label}
              </Btn>
            ))}
          </div>

          <div className="label">बातचीत</div>
          <div className="thread">
            {msgs.length === 0 && <div className="info-row">अभी कोई संदेश नहीं</div>}
            {msgs.map((m) => {
              const it = m.direction === 'in' ? INTENT[m.intent] || ['संदेश', 'neutral'] : null
              return (
                <div key={m.id} className={`msg ${m.direction === 'in' ? 'in' : 'out'}`}>
                  {m.text}
                  {m.direction === 'in' && m.transcript && m.transcript !== m.text && <div className="transcript">“{m.transcript}”</div>}
                  <div className="meta">
                    <span>{tgTime(m.tg_date)}</span>
                    {m.tg_date && <span>· Telegram समय</span>}
                    {m.status === 'pending' && <span className="chip ask sm">भेजना बाकी</span>}
                    {m.status === 'failed' && <span className="chip urgent sm">नहीं गया</span>}
                    {it && <span className={`chip ${it[1]} sm`}>{it[0]}</span>}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      <p className="lock-note"><Lock size={14} /> हर संदेश का कोड सेव है · ऐप सिर्फ़ तय संदेश भेजता है</p>

      {/* S3 risk notice before the first template goes to the thekedar */}
      <Sheet open={!!ask} onClose={() => setAsk(null)}>
        <h2>क्या यह ठेकेदार को भेजना है?</h2>
        <div className="card ask" style={{ padding: 14, marginTop: 10 }}>
          <div className="row" style={{ color: 'var(--ask)', fontWeight: 700 }}><TriangleAlert size={22} /> भेजने से पहले सुनें</div>
          <p style={{ margin: '8px 0 0' }}>भेजने से ठेकेदार को पता चलेगा कि आप अपना हिसाब रखते हैं। पहले यूनियन या सहायक को भेजना ज़्यादा सुरक्षित हो सकता है।</p>
        </div>
        <div className="btn-row" style={{ marginTop: 16 }}>
          <Btn variant="plain" className="narrow" onClick={() => setAsk(null)}>अभी नहीं</Btn>
          <Btn icon={Send} onClick={() => send(ask)}>भेजें</Btn>
        </div>
      </Sheet>

      <Sheet open={sent !== null} onClose={() => setSent(null)}>
        <h2>यह संदेश गया:</h2>
        <div className="quote" style={{ background: 'var(--cream)', marginTop: 10 }}><p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{sent}</p></div>
        <p className="small" style={{ marginTop: 10 }}>रक़म अनुमान है · बॉट बंद हो तो बाद में जाएगा</p>
        <Btn style={{ marginTop: 12 }} onClick={() => setSent(null)}>ठीक</Btn>
      </Sheet>
    </div>
  )
}
