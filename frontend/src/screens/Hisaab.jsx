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
  ZONE_UNCONFIRMED: 'ज़ोन पक्का नहीं — नीचे अपना ज़ोन चुनकर पक्का करें',
  CATEGORY_UNKNOWN: 'काम की श्रेणी पता नहीं — साथी या यूनियन से पूछकर भरें',
  SPHERE_UNKNOWN: 'काम सरकारी (केंद्र) है या नहीं, यह पक्का नहीं',
  RATE_NOT_FOUND: 'इस काम की सरकारी दर नहीं मिली',
  RATE_OUT_OF_WINDOW: 'इन तारीख़ों की सरकारी दर अभी हमारे पास नहीं',
  PIECE_RATE_UNSUPPORTED: 'ठेके (पीस-रेट) का हिसाब अभी नहीं होता',
}
const CAT_HI = { unskilled: 'अकुशल', semi_skilled: 'अर्ध-कुशल', skilled: 'कुशल', highly_skilled: 'अति-कुशल' }

const ZONES = [['I', 'महानगरपालिका सीमा'], ['II', 'नगर परिषद'], ['III', 'बाकी इलाका']]

export default function Hisaab() {
  const { profile, setProfile, go, toast } = useApp()
  const [h, setH] = useState(null)
  const [led, setLed] = useState(null) // confirmed days + payments, shown even when no amount can be computed
  const [zone, setZone] = useState(profile.site?.zone || 'I')
  const [savingZone, setSavingZone] = useState(false)
  const [why, setWhy] = useState(false)
  const [loadErr, setLoadErr] = useState(null) // request failed: show why + retry instead of an endless spinner
  const [tries, setTries] = useState(0)
  const today = todayIso()
  const d = new Date()
  const [from] = monthRange(d.getFullYear(), d.getMonth())

  useEffect(() => {
    let alive = true
    setLoadErr(null)
    read('cache:hisaab').then((c) => { if (alive && c && !h) setH(c) })
    api.hisaab(profile.worker_id, from, today)
      .then((r) => { if (alive) { setH(r); write('cache:hisaab', r) } })
      .catch((e) => { if (alive) setLoadErr(e instanceof api.NetworkError ? 'NETWORK' : e.code || 'ERROR') })
    api.ledger(profile.worker_id, from, today).then((r) => alive && setLed(r)).catch(() => {})
    return () => { alive = false }
  }, [profile.worker_id, from, today, tries])

  async function confirmZone() {
    setSavingZone(true)
    try {
      await api.apiJson('POST', '/api/sites/zone', { worker_id: profile.worker_id, zone })
      await setProfile({ ...profile, site: { ...profile.site, zone, zone_confirmed: true } })
      toast(`ज़ोन ${zone} पक्का हो गया`)
      setTries((n) => n + 1)
    } catch (e) {
      toast(e instanceof api.NetworkError ? 'हब से नहीं जुड़ पाए — फिर कोशिश करें' : `नहीं हो पाया (${e.code})`)
    } finally {
      setSavingZone(false)
    }
  }
  const errCodes = (h?.errors || []).map((e) => (typeof e === 'string' ? e : e.code))
  const records = [
    ...(led?.days || []).filter((x) => x.worked !== 'no').map((x) => ({ key: `d${x.entry_id}`, date: x.date, kind: 'day',
      text: `${x.start_time || '?'}–${x.end_time || '?'}${x.break_minutes ? ` · आराम ${x.break_minutes} मिनट` : ''}` })),
    ...(led?.payments || []).map((p) => ({ key: `p${p.entry_id}`, date: p.date, kind: 'pay', text: `${rupees(p.amount)} मिला` })),
  ].sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))

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

      {!h && !loadErr && <div className="row" style={{ marginTop: 20 }}><Spinner /> हब से हिसाब ला रहे हैं…</div>}
      {!h && loadErr && (
        <div className="card pad login-card" style={{ marginTop: 14 }}>
          <span className="icon-bubble login-bubble warn"><CircleAlert size={28} /></span>
          <div className="login-card-title">{loadErr === 'WORKER_NOT_FOUND' ? 'यह खाता हब पर नहीं मिला' : 'हिसाब नहीं आ पाया'}</div>
          <p className="login-card-text">
            {loadErr === 'WORKER_NOT_FOUND' ? 'सेटिंग्स से लॉग आउट करें और फिर से खाता बनाएँ या लॉग इन करें।'
              : loadErr === 'NETWORK' ? 'हब से नहीं जुड़ पाए। फ़ोन और हब एक ही Wi-Fi पर हों, फिर कोशिश करें।'
                : `नहीं हो पाया (${loadErr})`}
          </p>
          {loadErr === 'WORKER_NOT_FOUND'
            ? <Btn onClick={() => go('settings')}>सेटिंग्स खोलें</Btn>
            : <Btn onClick={() => setTries((n) => n + 1)}>फिर से कोशिश करें</Btn>}
        </div>
      )}

      {h && !h.ok && (
        <div className="card pad" style={{ marginTop: 14 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <CircleAlert size={22} color="var(--ask)" />
            <div>
              <div style={{ fontWeight: 700 }}>अभी रक़म नहीं दिखा सकते</div>
              {errCodes.map((code) => <div key={code} className="muted">{ERR[code] || code}</div>)}
            </div>
          </div>
          {errCodes.includes('ZONE_UNCONFIRMED') && (
            <div style={{ marginTop: 12 }}>
              <div className="toggle-chips" style={{ flexWrap: 'nowrap' }}>
                {ZONES.map(([z]) => (
                  <button key={z} className={`tchip ${zone === z ? 'on' : ''}`} style={{ flex: 1, padding: 0 }} onClick={() => setZone(z)}>ज़ोन {z}</button>
                ))}
              </div>
              <p className="small" style={{ margin: '8px 2px 10px', color: 'var(--text-2)' }}>
                {ZONES.find(([z]) => z === zone)?.[1]} · पता न हो तो साथी या यूनियन से पूछें
              </p>
              <Btn onClick={confirmZone} disabled={savingZone}>ज़ोन {zone} पक्का करें</Btn>
            </div>
          )}
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

      {records.length > 0 && (
        <div className="card how" style={{ marginTop: 14 }}>
          <div className="row between"><b style={{ fontSize: 17 }}>पक्के रिकॉर्ड</b><span className="small muted">{records.length}</span></div>
          {records.map((r) => (
            <div key={r.key} className="hrow">
              <span>{dayMonth(r.date)} · {r.kind === 'day' ? 'काम' : 'पैसा'}</span>
              <b>{r.text}</b>
            </div>
          ))}
          <button className="link" style={{ marginTop: 8 }} onClick={() => go('ledger')}>खाता में पूरा देखें</button>
        </div>
      )}
      {led && records.length === 0 && (
        <div className="info-row" style={{ marginTop: 14 }}><CircleAlert size={20} /> इस महीने अभी कोई पक्का रिकॉर्ड नहीं।</div>
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
