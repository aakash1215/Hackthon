// फ़ाइल tab (UI/ F1). The evidence packet arrives in P3; for now this shows what is already in the
// record (same style as F1's checklist) and links to settings (F2).
import { useEffect, useState } from 'react'
import { ChevronRight, CircleAlert, CircleCheck, Settings as Cog } from 'lucide-react'
import { TabBar, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'

export default function FileTab() {
  const { profile, go } = useApp()
  const [led, setLed] = useState(null)
  useEffect(() => { api.ledger(profile.worker_id).then(setLed).catch(() => {}) }, [profile.worker_id])

  const items = [
    { ok: !!(profile.site?.zone && profile.site?.zone_confirmed && profile.category), t: 'साइट, ज़ोन, श्रेणी पक्के' },
    { ok: (led?.days?.length || 0) > 0, t: `${led?.days?.length || 0} दिन का काम पक्का` },
    { ok: (led?.payments?.length || 0) > 0, t: `${led?.payments?.length || 0} बार पैसा दर्ज` },
    { ok: !!profile.thekedar?.phone, t: 'ठेकेदार का फ़ोन नंबर' },
    { ok: false, t: 'बिल्डर / साइट बोर्ड की फ़ोटो' },
    { ok: false, t: 'किसी साथी की गवाही' },
  ]
  return (
    <div className="screen with-tabs">
      <TopBar title="केस फ़ाइल" speakText="केस फ़ाइल" />
      <div className="card fields" style={{ marginTop: 6 }}>
        {items.map((it) => (
          <div key={it.t} className="frow" style={{ minHeight: 52 }}>
            {it.ok ? <CircleCheck size={24} color="var(--brand)" /> : <CircleAlert size={24} color="var(--ask)" />}
            <div className="grow" style={{ fontWeight: it.ok ? 400 : 700, color: it.ok ? 'var(--text-2)' : 'var(--text)', fontSize: 16.5 }}>{it.t}</div>
          </div>
        ))}
      </div>
      <div className="info-row" style={{ marginTop: 12 }}>
        <CircleAlert size={20} /> सबूत-फ़ाइल (PDF), गवाही और साइट-बोर्ड फ़ोटो जल्द यहाँ जुड़ेंगे। आपके अपने रिकॉर्ड से बनेगी — क़ानूनी सबूत की गारंटी नहीं।
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <button className="settings-row" onClick={() => go('settings')}>
          <span className="icon-bubble"><Cog size={20} /></span>
          <div className="grow"><div className="t">सेटिंग्स और सुरक्षा</div><div className="d">रिकॉर्ड की जाँच, भेजना बाकी, मंज़ूरी</div></div>
          <ChevronRight size={22} color="var(--text-2)" />
        </button>
      </div>
      <TabBar active="file" />
    </div>
  )
}
