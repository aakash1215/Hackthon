// Hisaab (UI/ H2). Every amount comes from the hub's deterministic wage engine; errors are codes.
// "समझाइए" shows the explanation on screen (TTS cut line: on-screen card + phone voice).
import { useEffect, useState } from 'react'
import { CalendarDays, CircleAlert, FileText, Mic, Volume2 } from 'lucide-react'
import { Btn, Sheet, Spinner, TabBar, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { read, write } from '../lib/db.js'
import { speak } from '../lib/device.js'
import { dayMonth, monthRange, rupees, todayIso } from '../lib/format.js'

const ERR = {
  SITE_NOT_SET: 'पहले काम की जगह भरें',
  NO_CONFIRMED_DAYS: 'अभी कोई पक्का दिन नहीं — पहले काम बोलकर पक्का करें',
  ZONE_UNCONFIRMED: 'ज़ोन पक्का नहीं — सेटिंग में ज़ोन पक्का करें',
  CATEGORY_UNKNOWN: 'काम की श्रेणी पता नहीं — साथी या यूनियन से पूछकर भरें',
  SPHERE_UNKNOWN: 'काम सरकारी (केंद्र) है या नहीं, यह पक्का नहीं',
  RATE_NOT_FOUND: 'इस काम की सरकारी दर नहीं मिली',
  RATE_OUT_OF_WINDOW: 'इन तारीख़ों की सरकारी दर अभी हमारे पास नहीं',
  PIECE_RATE_UNSUPPORTED: 'ठेके (पीस-रेट) का हिसाब अभी नहीं होता',
}
const CAT_HI = { unskilled: 'अकुशल', semi_skilled: 'अर्ध-कुशल', skilled: 'कुशल', highly_skilled: 'अति-कुशल' }

export default function Hisaab() {
  const { profile, go } = useApp()
  const [h, setH] = useState(null)
  const [why, setWhy] = useState(false)
  const today = todayIso()
  const d = new Date()
  const [from] = monthRange(d.getFullYear(), d.getMonth())

  useEffect(() => {
    let alive = true
    read('cache:hisaab').then((c) => { if (alive && c && !h) setH(c) })
    api.hisaab(profile.worker_id, from, today).then((r) => { if (alive) { setH(r); write('cache:hisaab', r) } }).catch(() => {})
    return () => { alive = false }
  }, [profile.worker_id, from, today])

  const t = h?.totals
  const prov = h?.provenance?.[0]
  const nDays = h?.days?.filter((x) => !x.error).length || 0
  const firstDay = h?.days?.[0]?.date
  const lastDay = h?.days?.[h.days.length - 1]?.date
  const explain = t ? `आपने ${nDays} दिन काम किया। सरकारी न्यूनतम दर से ${rupees(t.due_statutory, { decimals: true })} बनता है। आपको ${rupees(t.paid_total, { decimals: true })} मिले। लगभग ${rupees(t.claim_estimate)} अभी बाकी हो सकते हैं। यह अनुमान है।` : ''

  return (
    <div className="screen with-tabs">
      <TopBar title="हिसाब" speakText={explain || 'हिसाब'} />
      <div><span className="period-chip"><CalendarDays size={20} /> {firstDay && firstDay !== lastDay ? `${dayMonth(firstDay).split(' ')[0]}–${dayMonth(lastDay)}` : dayMonth(firstDay || today)}</span></div>

      {!h && <div className="row" style={{ marginTop: 20 }}><Spinner /> हब से हिसाब ला रहे हैं…</div>}

      {h && !h.ok && (
        <div className="card pad" style={{ marginTop: 14 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <CircleAlert size={22} color="var(--ask)" />
            <div>
              <div style={{ fontWeight: 700 }}>अभी रक़म नहीं दिखा सकते</div>
              {(h.errors || []).map((e) => {
                const code = typeof e === 'string' ? e : e.code
                return <div key={code} className="muted">{ERR[code] || code}</div>
              })}
            </div>
          </div>
        </div>
      )}

      {h?.ok && t && (
        <>
          <div className="hero">
            <div className="l">अभी तक बाकी</div>
            <div className="amt">{rupees(t.claim_estimate)} <span className="est">अनुमान</span></div>
            <div className="stats">
              <div><div className="k">बनता है</div><div className="v">{rupees(t.due_statutory)}</div></div>
              <div><div className="k">मिला</div><div className="v">{rupees(t.paid_total)}</div></div>
              <div><div className="k">काम के दिन</div><div className="v">{nDays}</div></div>
            </div>
          </div>

          <div className="card how">
            <div className="row between"><b style={{ fontSize: 17 }}>कैसे बना</b><button className="link" onClick={() => setWhy(true)}>क्यों?</button></div>
            <div className="hrow"><span>{nDays} दिन · सरकारी न्यूनतम दर से (ओवरटाइम दोगुनी दर)</span><b>{rupees(t.due_statutory, { decimals: true })}</b></div>
            {t.due_contractual && <div className="hrow"><span>तय मज़दूरी से</span><b>{rupees(t.due_contractual, { decimals: true })}</b></div>}
            <div className="hrow total"><span>कुल बनता है</span><b>{rupees(t.due_statutory, { decimals: true })}</b></div>
            <div className="hrow"><span>मिला</span><b>− {rupees(t.paid_total, { decimals: true })}</b></div>
          </div>

          {prov && (
            <div className="card soft source">
              <FileText size={24} color="var(--text-2)" />
              <div>
                <div className="k">सरकारी दर का स्रोत</div>
                <div className="t">अधिसूचना {String(prov.notification_no || '').split('/').pop()} · {prov.notification_date ? prov.notification_date.split('-').reverse().join('.') : ''}</div>
                <div className="m">ज़ोन {profile.site?.zone || '—'} · {CAT_HI[profile.category] || '—'} · बांधकाम · {prov.valid_from?.slice(8)}.{prov.valid_from?.slice(5, 7)}–{prov.valid_to?.split('-').reverse().join('.')}</div>
                {prov.verification_status && prov.verification_status !== 'VERIFIED' && (
                  <div className="warn"><CircleAlert size={18} /> मूल मराठी अधिसूचना से जाँचना बाकी</div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      <div className="bottom-actions" style={{ paddingTop: 4 }}>
        <Btn icon={Mic} onClick={() => go('hisaabCheck')}>ठेकेदार का हिसाब जाँचें</Btn>
        <Btn variant="outline" icon={Volume2} onClick={() => { setWhy(true); speak(explain) }} disabled={!t}>समझाइए</Btn>
      </div>

      <Sheet open={why} onClose={() => setWhy(false)}>
        <h2>यह रक़म कैसे बनी</h2>
        <p style={{ marginTop: 6 }}>{explain}</p>
        <p className="muted" style={{ fontSize: 14 }}>
          रोज़ की न्यूनतम मज़दूरी = महीने की सरकारी दर ÷ 26। 8 घंटे से ज़्यादा काम पर ओवरटाइम दोगुनी दर से। बाकी = बनता है − मिला।
        </p>
        {(h?.assumptions || []).length > 0 && (
          <div className="info-row" style={{ fontSize: 13.5 }}>
            <CircleAlert size={18} />
            <div>{h.assumptions.map((a) => <div key={a}>{a}</div>)}</div>
          </div>
        )}
        <p className="small" style={{ marginTop: 12 }}>सब रक़म अनुमान हैं — यह क़ानूनी सलाह नहीं है।</p>
        <Btn style={{ marginTop: 12 }} onClick={() => setWhy(false)}>ठीक है</Btn>
      </Sheet>
      <TabBar active="hisaab" />
    </div>
  )
}
