// हिसाब जाँचें (UI/ H3): the worker narrates, later and on her own, what the thekedar said.
// Below the H3 content (composed, same style): recording in front of the thekedar, with the notice
// first (BUILD_PLAN §8), and earlier checks (→ मिलान).
import { useEffect, useState } from 'react'
import { ChevronRight, Keyboard, Mic, Scale, ShieldAlert } from 'lucide-react'
import { Btn, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { dayMonth, localIso } from '../lib/format.js'

export default function HisaabCheck() {
  const { profile, go, back, toast } = useApp()
  const [busy, setBusy] = useState(false)
  const [past, setPast] = useState([])

  useEffect(() => {
    api.statements(profile.worker_id).then((r) => setPast(r.items || [])).catch(() => {})
  }, [profile.worker_id])

  async function typeIt() {
    setBusy(true)
    try {
      const r = await api.manualStatement(profile.worker_id, localIso())
      go('confirm', { entryId: r.entry_id })
    } catch (e) {
      toast(e instanceof api.NetworkError ? 'हब से जुड़ने पर ही — अभी बोलकर दर्ज करें' : `नहीं हो पाया (${e.code})`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <TopBar title="हिसाब जाँचें" onBack={back}
        speakText="ठेकेदार ने क्या कहा? उनकी बात अपने शब्दों में बोलिए। जैसे: 12 दिन, 600 रोज़, 2000 उचल काटी। यह आप ख़ुद, बाद में बोलें। ठेकेदार को चुपके से रिकॉर्ड न करें।" />
      <h1 className="title lg">ठेकेदार ने क्या कहा?</h1>
      <p className="subtitle">उनकी बात अपने शब्दों में बोलिए</p>

      <div className="card soft example">
        <div className="k">जैसे:</div>
        <div className="q">“12 दिन, 600 रोज़, 2000 उचल काटी”</div>
        <div className="s">दिन · रोज़ की दर · कटौती · कितना दिया</div>
      </div>

      <button className="mic-btn lg" onClick={() => go('record', { kind: 'hisaab_statement' })} aria-label="बोलना शुरू करें">
        <span><Mic size={40} /></span>
      </button>
      <div className="press">दबाएँ और बोलें</div>

      <div className="card ask warn-card">
        <ShieldAlert size={28} />
        <div>यह आप ख़ुद, बाद में बोलें। ठेकेदार को चुपके से रिकॉर्ड न करें।</div>
      </div>

      <div className="stack" style={{ marginTop: 16 }}>
        <Btn variant="plain" icon={Keyboard} onClick={typeIt} disabled={busy}>{busy ? 'खोल रहे हैं…' : 'टाइप करके भरें'}</Btn>
        <Btn variant="outline" icon={Mic} onClick={() => go('recordOther', { who: 'thekedar' })}>ठेकेदार के सामने रिकॉर्ड करें (सूचना के साथ)</Btn>
      </div>

      {past.length > 0 && (
        <div className="card pending">
          <div style={{ fontWeight: 700, color: 'var(--text-2)', fontSize: 14 }}>पिछले मिलान</div>
          {past.slice(0, 5).map((s) => (
            <button key={s.entry_id} className="item" onClick={() => go('diff', { entryId: s.entry_id })}>
              <span className="icon-bubble blue"><Scale size={18} /></span>
              <div className="grow">
                <div style={{ fontWeight: 700 }}>{s.speaker === 'thekedar' ? 'ठेकेदार की रिकॉर्डिंग' : 'आपने बताया'}{s.confirmed_at ? ` · ${dayMonth(s.confirmed_at.slice(0, 10))}` : ''}</div>
                <div className="small" style={{ color: 'var(--text-2)' }}>{s.count ? `${s.count} फ़र्क़ मिले` : 'कोई फ़र्क़ नहीं'}</div>
              </div>
              <ChevronRight size={20} color="var(--text-2)" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
