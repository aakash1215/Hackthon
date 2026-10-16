// Settings & safety (UI/ F2, the parts P2 needs): chain check, upload queue, language, audio consent.
// Not built yet: SMS record code, PIN, delete one/all (PIN is cut line §4 #7; deletes need the P3 tombstone UI).
import { useEffect, useState } from 'react'
import { Check, ChevronRight, CloudUpload, Languages, MessageCircle, Mic, RefreshCw, ShieldCheck, CircleAlert, Users } from 'lucide-react'
import { Btn, Sheet, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { flush, queueJson } from '../lib/sync.js'

export default function Settings() {
  const { profile, setProfile, sync, back, go, toast } = useApp()
  const [chain, setChain] = useState(null)
  const [unionSheet, setUnionSheet] = useState(false)
  const [unionDraft, setUnionDraft] = useState(profile.union_phone || '')
  const check = () => { setChain(null); api.chainVerify().then(setChain).catch(() => setChain({ offline: true })) }
  useEffect(check, [])

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
      </div>
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
      <p className="center small" style={{ marginTop: 'auto' }}>हब पर काम · आवाज़ पहले फ़ोन में सेव · संस्करण 0.2</p>
    </div>
  )
}
