// Settings & safety (UI/ F2, the parts P2 needs): chain check, upload queue, language, audio consent.
// Not built yet: SMS record code, PIN, delete one/all (PIN is cut line §4 #7; deletes need the P3 tombstone UI).
import { useEffect, useState } from 'react'
import { Check, ChevronRight, CloudUpload, Languages, LogOut, MessageCircle, Mic, RefreshCw, ShieldCheck, CircleAlert, Users, Zap } from 'lucide-react'
import { Btn, Sheet, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { clearPhone } from '../lib/db.js'
import { flush, queueJson } from '../lib/sync.js'

export default function Settings() {
  const { profile, setProfile, sync, back, go, toast } = useApp()
  const [chain, setChain] = useState(null)
  const [unionSheet, setUnionSheet] = useState(false)
  const [unionDraft, setUnionDraft] = useState(profile.union_phone || '')
  const [logoutSheet, setLogoutSheet] = useState(false)
  const [cloudOk, setCloudOk] = useState(null) // null = checking · true = the hub has CHAT_API_KEY set
  const [engineSheet, setEngineSheet] = useState(false)
  const [engineDraft, setEngineDraft] = useState('local')
  const check = () => { setChain(null); api.chainVerify().then(setChain).catch(() => setChain({ offline: true })) }
  useEffect(check, [])
  useEffect(() => { api.health().then((h) => setCloudOk(!!h?.cloud?.configured)).catch(() => setCloudOk(false)) }, [])
  const engine = profile.ai_engine === 'cloud' ? 'cloud' : 'local'

  async function saveEngine() {
    await setProfile({ ...profile, ai_engine: engineDraft })
    setEngineSheet(false)
    toast(engineDraft === 'cloud' ? 'तेज़ मोड चालू — ChatGPT API' : 'सस्ता मोड चालू — हब के अपने मॉडल')
  }

  async function toggleConsent() {
    const p = { ...profile, consent_keep_audio: !profile.consent_keep_audio }
    await setProfile(p)
    await queueJson('POST', '/api/workers', {
      id: p.worker_id, display_name: p.display_name || null, language: p.language === 'mr' ? 'mr' : 'hi', category: p.category,
      default_break_min: p.usual?.break_min ?? null, consent_keep_audio: p.consent_keep_audio, gps_opt_in: !!p.gps_opt_in,
    })
    toast('बदलाव सेव हो गया')
  }

  // P4: the union / helper number used by the "बातचीत रोक दी गई" call list. Stays on the phone.
  async function saveUnion() {
    await setProfile({ ...profile, union_phone: unionDraft.trim() || null })
    setUnionSheet(false)
    toast('नंबर सेव हो गया')
  }

  // Log out of this phone only: the hub keeps every saved entry and the hash chain.
  async function logout() {
    await clearPhone()
    window.location.replace('/')
  }

  return (
    <div className="screen">
      <TopBar title="सेटिंग्स और सुरक्षा" onBack={back} speakText="सेटिंग्स और सुरक्षा" />
      <div className={`status-card ${chain && !chain.ok && !chain.offline ? 'bad' : ''}`}>
        {chain && !chain.ok && !chain.offline ? <CircleAlert size={40} color="var(--urgent)" /> : <ShieldCheck size={40} />}
        <div className="grow">
          <div className="t">{!chain ? 'जाँच रहे हैं…' : chain.offline ? 'हब से जुड़ने पर जाँचेंगे' : chain.ok ? 'रिकॉर्ड की जाँच: सब सही' : `रिकॉर्ड बदला गया: एंट्री ${chain.broken_at_seq}`}</div>
          {chain?.ok && <div className="muted">{chain.events} एंट्री · कोई बदलाव नहीं मिला</div>}
        </div>
        <button className="chip ok" style={{ background: '#fff' }} onClick={check}>फिर जाँचें</button>
      </div>

      <div className="label">रिकॉर्ड</div>
      <div className="card">
        <button className="settings-row" onClick={() => { flush(); toast('भेज रहे हैं…') }}>
          <span className="icon-bubble"><CloudUpload size={20} /></span>
          <div className="grow"><div className="t">हब पर बैकअप</div><div className="d">{sync.queued ? `${sync.queued} रिकॉर्डिंग भेजना बाकी` : 'सब भेज दिया'}{sync.hub === false ? ' · हब नहीं मिला' : ''}</div></div>
          <RefreshCw size={20} color="var(--text-2)" />
        </button>
      </div>

      <div className="label">ठेकेदार</div>
      <div className="card">
        <button className="settings-row" onClick={() => go('telegram')}>
          <span className="icon-bubble"><MessageCircle size={20} /></span>
          <div className="grow"><div className="t">ठेकेदार से Telegram पर जुड़ें</div><div className="d">सिर्फ़ तय संदेश · हर संदेश सेव</div></div>
          <ChevronRight size={22} color="var(--text-2)" />
        </button>
        <button className="settings-row" onClick={() => { setUnionDraft(profile.union_phone || ''); setUnionSheet(true) }}>
          <span className="icon-bubble"><Users size={20} /></span>
          <div className="grow"><div className="t">यूनियन / सहायक का नंबर</div><div className="d">मुश्किल में एक टैप से कॉल</div></div>
          <span className="muted">{profile.union_phone || 'जोड़ें'}</span>
          <ChevronRight size={22} color="var(--text-2)" />
        </button>
      </div>

      <div className="label">आप और आपका डेटा</div>
      <div className="card">
        <div className="settings-row">
          <span className="icon-bubble"><Languages size={20} /></span>
          <div className="grow"><div className="t">भाषा</div></div>
          <span className="muted">{{ hi: 'हिंदी', mr: 'मराठी', en: 'English' }[profile.language] || 'हिंदी'}</span>
        </div>
        <button className="settings-row" onClick={toggleConsent}>
          <span className="icon-bubble"><Mic size={20} /></span>
          <div className="grow"><div className="t">आवाज़ रखने की मंज़ूरी</div></div>
          <span className="muted">{profile.consent_keep_audio ? 'हाँ' : 'नहीं'}</span>
          <ChevronRight size={22} color="var(--text-2)" />
        </button>
        <button className="settings-row" onClick={() => { setEngineDraft(engine); setEngineSheet(true) }}>
          <span className="icon-bubble"><Zap size={20} /></span>
          <div className="grow"><div className="t">AI: तेज़ या सस्ता</div><div className="d">आवाज़ पढ़ना, हिसाब भरना, सुनाना</div></div>
          <span className="muted">{engine === 'cloud' ? 'तेज़' : 'सस्ता'}</span>
          <ChevronRight size={22} color="var(--text-2)" />
        </button>
      </div>
      <Sheet open={engineSheet} onClose={() => setEngineSheet(false)}>
        <h2>AI कैसे चले?</h2>
        <div className="stack" style={{ marginTop: 10 }}>
          {[
            { v: 'local', n: 'सस्ता · मुफ़्त', s: 'हब के अपने (open-weight) मॉडल · बिना इंटरनेट · थोड़ा धीमा' },
            { v: 'cloud', n: 'तेज़ · ChatGPT API', off: cloudOk === false,
              s: cloudOk === false ? 'अभी बंद · हब पर ChatGPT key (CHAT_API_KEY) नहीं मिली या हब नहीं मिला'
                : 'जल्दी जवाब, साफ़ महिला आवाज़ · इंटरनेट चाहिए · हर बार पैसे लगते हैं' },
          ].map((o) => {
            const on = engineDraft === o.v
            return (
              <div key={o.v} className={`option ${on ? 'on' : ''}`} onClick={() => !o.off && setEngineDraft(o.v)} role="radio"
                aria-checked={on} aria-disabled={!!o.off} style={o.off ? { opacity: 0.55 } : undefined}>
                <div className="body">
                  <div className="name">{o.n}</div>
                  <div className="desc">{o.s}</div>
                </div>
                <span className={`radio ${on ? 'on' : ''}`}>{on && <Check size={13} strokeWidth={3} />}</span>
              </div>
            )
          })}
        </div>
        {engineDraft === 'cloud' && (
          <div className="info-row" style={{ marginTop: 12, background: 'var(--ask-bg)', color: 'var(--ask)' }}>
            <CircleAlert size={20} /> आपकी आवाज़ और उसका लिखा हुआ हिसाब इंटरनेट से OpenAI (ChatGPT) के सर्वर पर जाएगा। मूल रिकॉर्डिंग पहले हब पर सेव और हैश होती है। ChatGPT न चले तो हब के अपने मॉडल अपने-आप काम करेंगे।
          </div>
        )}
        <div className="btn-row" style={{ marginTop: 16 }}>
          <Btn variant="plain" className="narrow" onClick={() => setEngineSheet(false)}>रद्द</Btn>
          <Btn icon={Check} onClick={saveEngine}>सेव करें</Btn>
        </div>
      </Sheet>
      <Sheet open={unionSheet} onClose={() => setUnionSheet(false)}>
        <h2>यूनियन / सहायक का नंबर</h2>
        <div className="field" style={{ marginTop: 10 }}>
          <input type="tel" inputMode="tel" autoFocus value={unionDraft} maxLength={15} onChange={(e) => setUnionDraft(e.target.value.replace(/[^\d+]/g, ''))} />
        </div>
        <div className="btn-row" style={{ marginTop: 16 }}>
          <Btn variant="plain" className="narrow" onClick={() => setUnionSheet(false)}>रद्द</Btn>
          <Btn icon={Check} onClick={saveUnion}>सेव करें</Btn>
        </div>
      </Sheet>
      {/* same place and style as F2's red "सब मिटाएँ" button */}
      <Btn variant="danger" icon={LogOut} style={{ marginTop: 18 }} onClick={() => setLogoutSheet(true)}>लॉग आउट</Btn>
      <Sheet open={logoutSheet} onClose={() => setLogoutSheet(false)}>
        <div className="kicker" style={{ color: 'var(--urgent)' }}><LogOut size={20} /> लॉग आउट</div>
        <h2>इस फ़ोन से {profile.display_name || 'आपका'} खाता हटाएँ?</h2>
        <p className="muted" style={{ marginTop: 0 }}>हब पर आपका पूरा रिकॉर्ड सुरक्षित रहेगा। इस फ़ोन पर फिर से शुरू से जानकारी भरनी होगी।</p>
        {sync.queued > 0 && (
          <div className="info-row" style={{ background: 'var(--urgent-bg)', color: 'var(--urgent)' }}>
            <CircleAlert size={20} /> {sync.queued} रिकॉर्डिंग अभी हब पर नहीं पहुँची — लॉग आउट करने पर ये खो जाएँगी। पहले हब से जुड़कर भेजें।
          </div>
        )}
        <div className="stack" style={{ marginTop: 16 }}>
          {sync.queued > 0 && <Btn icon={CloudUpload} onClick={() => { flush(); setLogoutSheet(false); toast('भेज रहे हैं…') }}>पहले भेजें</Btn>}
          <Btn variant="danger" icon={LogOut} onClick={logout}>{sync.queued > 0 ? 'फिर भी लॉग आउट करें' : 'हाँ, लॉग आउट करें'}</Btn>
          <Btn variant="plain" onClick={() => setLogoutSheet(false)}>रद्द करें</Btn>
        </div>
      </Sheet>
      <p className="center small" style={{ marginTop: 'auto', paddingTop: 16 }}>हब पर काम · आवाज़ पहले फ़ोन में सेव · संस्करण 0.2</p>
    </div>
  )
}
