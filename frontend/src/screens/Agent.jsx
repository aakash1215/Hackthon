// सहायक (agent) tab. Composed screen (not in UI/), built from existing components: TopBar, card, chip, field,
// Btn, VoiceInput, TabBar. The hub classifies the question and answers from fixed templates filled with the
// worker's own record (backend/app/agent.py). Messages to the thekedar are only *offered*; the worker taps to send.
import { useEffect, useRef, useState } from 'react'
import { Bot, Check, ChevronRight, Phone, Send, ShieldCheck, Volume2 } from 'lucide-react'
import { Btn, Spinner, TabBar, TopBar, useApp } from '../components/Ui.jsx'
import VoiceInput from '../components/VoiceInput.jsx'
import * as api from '../lib/api.js'
import { read, write } from '../lib/db.js'
import { getEngine } from '../lib/engine.js'
import { speak } from '../lib/device.js'

const HELLO = 'नमस्ते! मैं आपकी सहायक हूँ। आपके अपने रिकॉर्ड से जवाब देती हूँ — कितने दिन काम किया, कितना पैसा मिला, कितना बाकी हो सकता है। ठेकेदार को सिर्फ़ तय संदेश भेजती हूँ, वह भी आपके कहने पर।'
const CHIPS = [
  { t: 'मेरा कितना पैसा बाकी है?', intent: 'money_due' },
  { t: 'इस हफ़्ते कितने दिन काम किया?', intent: 'days_worked', period: 'this_week' },
  { t: 'अब तक कितने पैसे मिले?', intent: 'paid_total' },
  { t: 'मेरी सरकारी मज़दूरी कितनी है?', intent: 'min_wage' },
  { t: 'ठेकेदार ने क्या जवाब दिया?', intent: 'thekedar_status' },
  { t: 'ठेकेदार को हिसाब भेजो', intent: 'send_summary' },
]
const TG_ERR = {
  NOT_LINKED: 'ठेकेदार अभी जुड़े नहीं हैं',
  PAUSED: 'बातचीत रुकी है — पहले फिर चालू करें',
  DAILY_LIMIT: 'आज के 5 संदेश हो गए — कल फिर भेजें',
}
const CACHE = 'cache:agent'

export default function Agent() {
  const { profile, go, toast } = useApp()
  const [msgs, setMsgs] = useState([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const end = useRef(null)

  useEffect(() => { read(CACHE).then((m) => { if (Array.isArray(m)) setMsgs(m) }) }, [])
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [msgs, busy])

  const push = (m) => setMsgs((xs) => {
    const next = [...xs, { id: crypto.randomUUID(), ...m }].slice(-40)
    write(CACHE, next)
    return next
  })
  const patch = (id, p) => setMsgs((xs) => {
    const next = xs.map((m) => (m.id === id ? { ...m, ...p } : m))
    write(CACHE, next)
    return next
  })

  async function ask(q, chip) {
    const question = (q || '').trim()
    if (!question || busy) return
    push({ who: 'me', text: question })
    setText('')
    setBusy(true)
    try {
      const r = await api.agentAsk({
        worker_id: profile.worker_id, text: question, engine: getEngine(),
        ...(chip ? { intent: chip.intent, period: chip.period || 'all' } : {}),
      })
      push({ who: 'agent', text: r.text, actions: r.actions || [], suggestions: r.suggestions || [] })
    } catch (e) {
      push({ who: 'agent', text: e instanceof api.NetworkError ? 'हब से नहीं जुड़ पाई। फ़ोन और हब एक ही Wi-Fi पर हों, फिर पूछें।' : `अभी जवाब नहीं दे पाई (${e.code || 'error'})।`, actions: [] })
    } finally {
      setBusy(false)
    }
  }

  async function act(m, a) {
    if (a.type === 'go') return go(a.screen, a.params || {})
    if (a.type === 'call_union') {
      if (profile.union_phone) window.location.href = `tel:${profile.union_phone}`
      else { toast('पहले सेटिंग्स में यूनियन / सहायक का नंबर जोड़ें'); go('settings') }
      return
    }
    if (a.type === 'tg_send') {
      patch(m.id, { sending: a.template })
      try {
        await api.telegramSend(profile.worker_id, a.template)
        patch(m.id, { sending: null, sent: a.template })
        push({ who: 'agent', text: 'भेज दिया। तय संदेश ठेकेदार को Telegram पर गया और रिकॉर्ड में सेव हुआ। जवाब आने पर ‘आज’ पर दिखेगा।', actions: [] })
      } catch (e) {
        patch(m.id, { sending: null })
        toast(TG_ERR[e.code] || (e instanceof api.NetworkError ? 'हब से नहीं जुड़ पाए' : `नहीं भेज पाए (${e.code})`))
      }
    }
  }

  return (
    <div className="screen with-tabs agent-screen">
      <TopBar title="सहायक" speakText={HELLO} />

      <div className="agent-msg">
        <span className="icon-bubble blue"><Bot size={20} /></span>
        <div className="agent-bubble">
          <p>{HELLO}</p>
          <button className="speaker" onClick={() => speak(HELLO)} aria-label="सुनें"><Volume2 size={18} /></button>
          <div className="agent-trust"><ShieldCheck size={16} /> जवाब आपके अपने रिकॉर्ड से · ठेकेदार को सिर्फ़ तय संदेश</div>
        </div>
      </div>

      {msgs.map((m) => (m.who === 'me' ? (
        <div key={m.id} className="me-bubble">{m.text}</div>
      ) : (
        <div key={m.id} className="agent-msg">
          <span className="icon-bubble blue"><Bot size={20} /></span>
          <div className="agent-bubble">
            <p>{m.text}</p>
            <button className="speaker" onClick={() => speak(m.text)} aria-label="सुनें"><Volume2 size={18} /></button>
            {m.actions?.length > 0 && (
              <div className="stack agent-actions">
                {m.actions.map((a) => {
                  if (a.type === 'tg_send') {
                    if (m.sent === a.template) return <div key={a.label} className="chip ok"><Check size={16} /> भेज दिया</div>
                    return <Btn key={a.label} icon={m.sending ? undefined : Send} disabled={!!m.sending} onClick={() => act(m, a)}>{m.sending ? <Spinner /> : a.label}</Btn>
                  }
                  if (a.type === 'call_union') return <Btn key={a.label} variant="danger" icon={Phone} onClick={() => act(m, a)}>{a.label}</Btn>
                  return (
                    <button key={a.label} className="agent-link" onClick={() => act(m, a)}>
                      {a.label} <ChevronRight size={18} />
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )))}

      {busy && <div className="agent-msg"><span className="icon-bubble blue"><Bot size={20} /></span><div className="agent-bubble"><Spinner /></div></div>}

      <div ref={end} />

      {/* docked above the tab bar, like a chat app: suggestion chips (scroll sideways) + the question box */}
      <div className="agent-dock">
        <div className="agent-chips">
          {CHIPS.map((c) => <button key={c.t} className="chip blue" disabled={busy} onClick={() => ask(c.t, c)}>{c.t}</button>)}
        </div>
        <form className="agent-input" onSubmit={(e) => { e.preventDefault(); ask(text) }}>
          <div className="field grow">
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder="अपना सवाल लिखें या बोलें" maxLength={300} enterKeyHint="send" />
            <VoiceInput field="question" language={profile.language === 'mr' ? 'mr' : 'hi'} keepAudio={!!profile.consent_keep_audio}
              onText={(t) => ask(t)} label="बोलकर पूछें" />
          </div>
          <button type="submit" className="agent-send" disabled={busy || !text.trim()} aria-label="भेजें"><Send size={22} /></button>
        </form>
      </div>
      <TabBar active="agent" />
    </div>
  )
}
