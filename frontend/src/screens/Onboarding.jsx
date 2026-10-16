// Onboarding (O2, O3, O4 PIN, O5, O6, O7) login (UI/ A1) is the start page.
// Composed additions in the same style: name field (O5), GPS opt-in card (O6), 4th consent bullet (GPS).
import { useEffect, useState } from 'react'
import {
  Axe, NotebookPen, Plus, BrickWall, Check, ChevronDown, CircleHelp, Hammer, Info, MapPin,
  PaintRoller, Pencil, RefreshCw, Send, ShieldCheck, Shovel, Smartphone, Trash2, UserPlus, UserRound, Volume2, WifiOff, ArrowRight,
} from 'lucide-react'
import { Btn, Spinner, TopBar, useApp } from '../components/Ui.jsx'
import PinPad from '../components/PinPad.jsx'
import VoiceInput from '../components/VoiceInput.jsx'
import * as api from '../lib/api.js'
import { clearLocalData, profileFromServer } from '../lib/profile.js'
import { getFix, speak } from '../lib/device.js'
import { queueJson } from '../lib/sync.js'

const STEPS = ['language', 'consent', 'pin', 'category', 'site', 'contractor']

export default function Onboarding() {
  const { setProfile } = useApp()
  const [step, setStep] = useState(0)
  const [login, setLogin] = useState(true) // login (A1) is the start page
  const [d, setD] = useState({
    // Answers the worker must give start empty (no pre-picked category or sphere): never invent values.
    language: 'hi', consent_keep_audio: true, display_name: '', category_label: null, category: null,
    category_confirmed: false, site: { name: '', landmark: '', city: 'छत्रपति संभाजीनगर', zone: 'I', zone_confirmed: false, sphere: null },
    gps: null, gps_opt_in: false, thekedar: { name: '', phone: '', phone_unknown: false },
    usual: { start: '09:00', end: '19:00', break_min: 60 }, agreed_daily: '', wage_period: 'weekly',
  })
  const up = (patch) => setD((x) => ({ ...x, ...patch }))
  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1))
  const back = () => (step === 0 ? setLogin(true) : setStep((s) => s - 1))
  const progress = { step: step + 1, total: 7 }

  async function finish() {
    const workerId = crypto.randomUUID().replace(/-/g, '').slice(0, 12)
    const p = { ...d, worker_id: workerId, onboarded: true, created: new Date().toISOString() }
    await clearLocalData() // a new account starts clean: no earlier person's records, queue or caches
    // (before the queueJson calls below, which this would otherwise wipe)
    // Profile writes are queued like recordings, so onboarding also works without the hub.
    await queueJson('POST', '/api/workers', {
      id: workerId, display_name: d.display_name.trim(), language: d.language === 'mr' ? 'mr' : 'hi',
      category: d.category, default_break_min: d.usual.break_min, consent_keep_audio: d.consent_keep_audio,
      gps_opt_in: d.gps_opt_in,
    })
    if (d.pin) await queueJson('POST', `/api/workers/${workerId}/pin`, { pin: d.pin }) // stored hashed on the hub
    await queueJson('POST', '/api/sites', {
      worker_id: workerId, name: d.site.name.trim(), landmark: d.site.landmark.trim() || null, city: d.site.city,
      state: 'Maharashtra', sphere: d.site.sphere, zone: d.site.zone, zone_confirmed: d.site.zone_confirmed,
      employment_sn: 11, wage_period: d.wage_period,
      ...(d.gps_opt_in && d.gps ? { site_lat: d.gps.lat, site_lon: d.gps.lon, site_gps_accuracy_m: d.gps.acc } : {}),
    })
    if (d.thekedar.name) {
      await queueJson('POST', '/api/parties', {
        worker_id: workerId, role: 'contractor', name: d.thekedar.name.trim(),
        phone: d.thekedar.phone_unknown ? null : d.thekedar.phone || null, source: 'stated',
      })
    }
    const { pin: _pin, ...profile } = p // the PIN never stays on the phone
    await setProfile(profile)
  }

  if (login) return <Login onNew={() => { setLogin(false); setStep(0) }} />
  const S = { language: Language, consent: Consent, pin: PinStep, category: Category, site: Site, contractor: Contractor }[STEPS[step]]
  return <S d={d} up={up} next={next} back={back} progress={progress} finish={finish} />
}

// Required-field gate for a step: errors show only after the first "आगे बढ़ें" tap.
function useRequired(errs, onOk) {
  const { toast } = useApp()
  const [tried, setTried] = useState(false)
  const go = () => {
    if (Object.values(errs).some(Boolean)) { setTried(true); toast('लाल निशान वाली बातें भरें'); return }
    onOk()
  }
  return { show: (k) => (tried ? errs[k] : null), go }
}

function Need({ msg }) {
  return msg ? <p className="err field-err">{msg}</p> : null
}

const NAME_OK = (s) => s.trim().length >= 2

// O4: create a 4-digit PIN (enter twice).
function PinStep({ d, up, next, back, progress }) {
  const [first, setFirst] = useState(null)
  const [err, setErr] = useState(0)
  function done(pin) {
    if (!first) { setFirst(pin); return }
    if (pin === first) { up({ pin }); next(); return }
    setFirst(null)
    setErr((e) => e + 1)
  }
  return (
    <div className="screen">
      <TopBar onBack={back} progress={progress} speakText={first ? 'वही PIN फिर से डालें' : '4 अंकों का PIN बनाएँ। फ़ोन किसी और के हाथ में हो, तो भी आपका हिसाब सुरक्षित रहे।'} />
      <h1 className="title">{first ? 'वही PIN फिर डालें' : '4 अंकों का PIN बनाएँ'}</h1>
      <p className="subtitle">{err && !first ? 'दोनों PIN अलग थे — फिर से बनाएँ' : 'फ़ोन किसी और के हाथ में हो, तो भी आपका हिसाब सुरक्षित रहे'}</p>
      <PinPad onDone={done} resetKey={`${first}-${err}-${d.pin}`} error={err} />
      <p className="center small" style={{ marginTop: 14 }}>यह PIN किसी को न बताएँ</p>
    </div>
  )
}

// A1: who is using the app? Pick your name, then your PIN. Needs the hub (the account lives there).
function Login({ onNew }) {
  const { setProfile, toast } = useApp()
  const [people, setPeople] = useState(null)
  const [sel, setSel] = useState(null)
  const [msg, setMsg] = useState(null)
  const [tries, setTries] = useState(0)
  const [busy, setBusy] = useState(false)

  const [loadKey, setLoadKey] = useState(0)

  useEffect(() => {
    setPeople(null)
    api.apiJson('GET', '/api/workers/directory', null, { timeoutMs: 6000 })
      .then((r) => { setPeople(r.items); if (r.items.length) setSel(r.items[0]) })
      .catch(() => setPeople(false))
  }, [loadKey])

  async function enter(res) {
    await clearLocalData()
    await setProfile(profileFromServer(res))
  }

  // One PIN entry at login. An account without a PIN yet sets it with this same entry (no confirm screen).
  async function tryLogin(pin) {
    setBusy(true)
    try {
      const res = await api.apiJson('POST', '/api/login', { worker_id: sel.id, pin: sel.has_pin ? pin : null })
      if (res.needs_pin) {
        await api.apiJson('POST', `/api/workers/${sel.id}/pin`, { pin })
        toast('PIN बन गया')
      }
      await enter(res)
    } catch (e) {
      const code = e.code || ''
      if (code.startsWith('WRONG_PIN')) setMsg(`PIN गलत · ${code.split(':')[1]} कोशिश बाकी`)
      else if (code.startsWith('LOCKED')) setMsg('बहुत बार गलत PIN — 5 मिनट बाद फिर कोशिश करें')
      else setMsg(e instanceof api.NetworkError ? 'हब से नहीं जुड़ पाए' : `नहीं हो पाया (${code})`)
      setTries((t) => t + 1)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <TopBar speakText="कौन इस्तेमाल कर रहा है? अपना नाम चुनें, फिर PIN डालें।" />
      <div className="login-logo"><NotebookPen size={36} /></div>
      <h1 className="login-title">कौन इस्तेमाल कर रहा है?</h1>
      {people === null && (
        <div className="login-state"><Spinner /><p className="muted" style={{ margin: 0 }}>खाते खोल रहे हैं…</p></div>
      )}
      {people === false && (
        <div className="login-state">
          <div className="card pad login-card">
            <span className="icon-bubble login-bubble warn"><WifiOff size={28} /></span>
            <div className="login-card-title">हब से नहीं जुड़ पाए</div>
            <p className="login-card-text">आपका खाता हब पर रहता है। फ़ोन और हब एक ही Wi-Fi पर हों, फिर कोशिश करें।</p>
            <Btn icon={RefreshCw} onClick={() => setLoadKey((k) => k + 1)}>फिर से कोशिश करें</Btn>
          </div>
          <Btn variant="outline" icon={UserPlus} onClick={onNew}>नया खाता बनाएँ</Btn>
        </div>
      )}
      {people && people.length === 0 && (
        <div className="login-state">
          <div className="card pad login-card">
            <span className="icon-bubble login-bubble"><UserRound size={28} /></span>
            <div className="login-card-title">अभी कोई खाता नहीं बना</div>
            <p className="login-card-text">इस हब पर पहला खाता बनाएँ — 2 मिनट लगेंगे।</p>
            <Btn icon={UserPlus} onClick={onNew}>नया खाता बनाएँ</Btn>
          </div>
        </div>
      )}
      {people && people.length > 0 && (
        <>
          <div className="who-row">
            {people.map((w) => (
              <button key={w.id} className={`who ${sel?.id === w.id ? 'on' : ''}`} onClick={() => { setSel(w); setMsg(null) }}>
                <span className="who-av">{w.initial}</span>
                <span className="who-name">{w.display_name}</span>
              </button>
            ))}
            <button className="who" onClick={onNew}>
              <span className="who-av"><Plus size={30} /></span>
              <span className="who-name">नया</span>
            </button>
          </div>
          {sel && (
            <>
              <p className={`center ${msg ? 'err' : 'muted'}`} style={{ margin: '14px 0 6px' }}>
                {msg || (sel.has_pin ? `${sel.display_name} — अपना PIN डालें` : `${sel.display_name} — नया 4 अंकों का PIN बनाएँ`)}
              </p>
              <PinPad onDone={tryLogin} resetKey={`${sel.id}-${tries}`} error={tries} disabled={busy}
                leftSlot={sel.has_pin ? <button className="link" onClick={() => toast('PIN भूल गए? यूनियन / सहायक की मदद से हब पर नया PIN बनवाएँ')}>भूल गए?</button> : null} />
            </>
          )}
        </>
      )}
      <div className="trust-line" style={{ marginTop: 'auto', paddingTop: 16 }}><ShieldCheck size={20} /> PIN सिर्फ़ आपके पास · हब पर छिपाकर (hash) रखा जाता है</div>
    </div>
  )
}

const LANGS = [
  { id: 'hi', letter: 'अ', name: 'हिंदी', desc: 'इस भाषा में चलाएँ?', speakLang: 'hi-IN' },
  { id: 'mr', letter: 'म', name: 'मराठी', desc: 'या भाषेत वापरायचे?', speakLang: 'mr-IN' },
  { id: 'en', letter: 'A', name: 'English', desc: 'Use the app in English', speakLang: 'en-IN' },
]

function Language({ d, up, next, back, progress }) {
  return (
    <div className="screen">
      <TopBar onBack={back} progress={progress} speakText="अपनी भाषा चुनें" />
      <h1 className="title">अपनी भाषा चुनें</h1>
      <p className="subtitle">Choose your language · तुमची भाषा निवडा</p>
      <div className="stack">
        {LANGS.map((l) => {
          const on = d.language === l.id
          return (
            <div key={l.id} className={`option ${on ? 'on' : ''}`} onClick={() => up({ language: l.id })} role="radio" aria-checked={on}>
              <span className={`avatar ${on ? 'brand' : ''}`}>{l.letter}</span>
              <div className="body">
                <div className="name">{l.name}</div>
                <div className="desc">{l.desc}</div>
              </div>
              <button className="speaker" onClick={(e) => { e.stopPropagation(); speak(l.desc, l.speakLang) }} aria-label="सुनें">
                <Volume2 size={18} />
              </button>
              <span className={`radio ${on ? 'on' : ''}`}>{on && <Check size={13} strokeWidth={3} />}</span>
            </div>
          )
        })}
        <div className="info-row"><Info size={20} /> बाद में सेटिंग्स से भाषा बदल सकते हैं।</div>
      </div>
      <div className="bottom-actions">
        <Btn icon={ArrowRight} onClick={next}>आगे बढ़ें</Btn>
      </div>
    </div>
  )
}

function Consent({ d, up, next, back, progress }) {
  const bullets = [
    { i: Smartphone, t: 'आपकी आवाज़ और हिसाब इस फ़ोन और आपके हिसाब-हब में ही रहते हैं' },
    { i: Send, t: 'ठेकेदार को आपकी मर्ज़ी के बिना कुछ नहीं भेजा जाएगा' },
    { i: MapPin, t: 'जगह (GPS) सिर्फ़ आपकी इजाज़त से, और आपको दिखाकर' },
    { i: Trash2, t: 'जब चाहें, कुछ भी या सब कुछ मिटा सकते हैं' },
  ]
  return (
    <div className="screen">
      <TopBar onBack={back} progress={progress} speakText={`आपकी मंज़ूरी। ${bullets.map((b) => b.t).join('। ')}`} />
      <h1 className="title">आपकी मंज़ूरी</h1>
      <p className="subtitle">शुरू करने से पहले ये चार बातें सुन लें</p>
      <div className="bullets">
        {bullets.map(({ i: I, t }) => (
          <div className="row" key={t}>
            <span className="icon-bubble cream"><I size={18} /></span>
            <p>{t}</p>
          </div>
        ))}
      </div>
      <div className="card-title" style={{ fontWeight: 700, fontSize: 18, margin: '8px 0 10px' }}>क्या आपकी आवाज़ की रिकॉर्डिंग रखें?</div>
      <div className="stack">
        {[
          { v: true, n: 'हाँ, आवाज़ रखें', s: 'मज़बूत रिकॉर्ड — यही सुझाव है', cls: 'good' },
          { v: false, n: 'नहीं, सिर्फ़ लिखा हुआ रखें', s: 'कमज़ोर रिकॉर्ड', cls: 'weak' },
        ].map((o) => {
          const on = d.consent_keep_audio === o.v
          return (
            <div key={String(o.v)} className={`option ${on ? 'on' : ''}`} onClick={() => up({ consent_keep_audio: o.v })} role="radio" aria-checked={on}>
              <div className="body">
                <div className="name">{o.n}</div>
                <div className={`desc ${o.cls}`}>{o.s}</div>
              </div>
              <span className={`radio ${on ? 'on' : ''}`}>{on && <Check size={13} strokeWidth={3} />}</span>
            </div>
          )
        })}
      </div>
      <div className="bottom-actions">
        <Btn icon={Check} onClick={next}>मैं सहमत हूँ</Btn>
      </div>
    </div>
  )
}

// Category → rate-pack category. The worker confirms; "पता नहीं" leaves it unset (engine returns CATEGORY_UNKNOWN).
const CATS = [
  { id: 'helper', n: 'हेल्पर / बेलदार', i: Shovel, cat: 'unskilled', label: 'अकुशल' },
  { id: 'mistri', n: 'मिस्त्री', i: BrickWall, cat: 'skilled', label: 'कुशल' },
  { id: 'carpenter', n: 'बढ़ई', i: Axe, cat: 'semi_skilled', label: 'अर्ध-कुशल' },
  { id: 'bar', n: 'सरिया वाला', i: Hammer, cat: 'semi_skilled', label: 'अर्ध-कुशल' },
  { id: 'painter', n: 'पेंटर', i: PaintRoller, cat: 'semi_skilled', label: 'अर्ध-कुशल' },
  { id: 'unknown', n: 'पता नहीं', i: CircleHelp, cat: null, label: 'पता नहीं' },
]

function Category({ d, up, next, back, progress }) {
  const sel = CATS.find((c) => c.id === d.category_label) || null
  const req = useRequired({
    name: !NAME_OK(d.display_name) && 'अपना नाम लिखें — लॉग इन में यही दिखेगा',
    cat: !sel && 'अपना काम चुनें — पता न हो तो ‘पता नहीं’ दबाएँ',
  }, next)
  return (
    <div className="screen">
      <TopBar onBack={back} progress={progress} speakText="आप क्या काम करते हैं? तस्वीर पर टैप करें" />
      <h1 className="title">आप क्या काम करते हैं?</h1>
      <p className="subtitle">तस्वीर पर टैप करें</p>
      <div className="label" style={{ marginTop: 0 }}>आपका नाम</div>
      <div className={`field ${req.show('name') ? 'invalid' : ''}`}>
        <input value={d.display_name} onChange={(e) => up({ display_name: e.target.value })} placeholder="नाम लिखें या बोलें" maxLength={40} />
        <VoiceInput field="name" language={d.language} keepAudio={d.consent_keep_audio} onText={(v) => up({ display_name: v })} />
      </div>
      <Need msg={req.show('name')} />
      <div className="grid-2" style={{ marginTop: 14 }}>
        {CATS.map((c) => {
          const on = c.id === sel?.id
          const I = c.i
          return (
            <button key={c.id} className={`tile ${on ? 'on' : ''}`} onClick={() => up({ category_label: c.id, category: c.cat, category_confirmed: false })}>
              {on && <span className="tick"><Check size={14} strokeWidth={3} /></span>}
              <span className="bubble"><I size={24} /></span>
              <span className="name">{c.n}</span>
            </button>
          )
        })}
      </div>
      <Need msg={req.show('cat')} />
      {sel && (
        <div className="card ask ask-card" style={{ marginTop: 14 }}>
          <div className="grow">
            <div className="title">आपकी श्रेणी: {sel.label}</div>
            <div className="sub">{sel.n} का काम — साथी से पक्का कर लें</div>
          </div>
          <button className={`chip ${d.category_confirmed ? 'ok' : 'ask'}`} onClick={() => up({ category_confirmed: !d.category_confirmed })}>
            {d.category_confirmed ? <><Check size={16} /> पक्का</> : <><CircleHelp size={16} /> पक्का करें</>}
          </button>
        </div>
      )}
      <div className="bottom-actions">
        <Btn icon={ArrowRight} onClick={req.go}>आगे बढ़ें</Btn>
      </div>
    </div>
  )
}

const CITIES = ['छत्रपति संभाजीनगर', 'पुणे', 'मुंबई', 'नागपुर', 'नाशिक', 'ठाणे', 'अन्य']
const ZONE_TEXT = { I: 'ज़ोन I — महानगरपालिका सीमा', II: 'ज़ोन II — नगर परिषद', III: 'ज़ोन III — बाकी इलाका' }

function Site({ d, up, next, back, progress }) {
  const { toast } = useApp()
  const [locating, setLocating] = useState(false)
  const site = d.site
  const setSite = (patch) => up({ site: { ...site, ...patch } })
  const suggested = site.city !== 'अन्य'
  const req = useRequired({
    name: !NAME_OK(site.name) && 'साइट का नाम लिखें',
    zone: !site.zone && 'ज़ोन चुनें — पता न हो तो साथी या यूनियन से पूछें',
    sphere: !site.sphere && 'हाँ / नहीं / पता नहीं में से एक चुनें',
  }, next)

  async function addGps() {
    setLocating(true)
    const fix = await getFix()
    setLocating(false)
    if (!fix) { toast('GPS नहीं मिला — फ़ोन में लोकेशन की इजाज़त दें'); return }
    up({ gps: fix, gps_opt_in: true })
  }

  return (
    <div className="screen">
      <TopBar onBack={back} progress={progress} speakText="काम की जगह। साइट का नाम और पास की पहचान बताएँ" />
      <h1 className="title">काम की जगह</h1>
      <p className="subtitle">बस नाम और पहचान — GPS आपकी मर्ज़ी से</p>
      <div className="label" style={{ marginTop: 0 }}>साइट का नाम</div>
      <div className={`field ${req.show('name') ? 'invalid' : ''}`}><input value={site.name} onChange={(e) => setSite({ name: e.target.value })} placeholder="जैसे: एग्ज़ाम्पल हाइट्स" maxLength={60} /><VoiceInput field="name" language={d.language} keepAudio={d.consent_keep_audio} onText={(v) => setSite({ name: v })} /></div>
      <Need msg={req.show('name')} />
      <div className="label">पास की पहचान</div>
      <div className="field"><input value={site.landmark} onChange={(e) => setSite({ landmark: e.target.value })} placeholder="जैसे: बस स्टैंड के पीछे" maxLength={60} /><VoiceInput field="text" language={d.language} keepAudio={d.consent_keep_audio} onText={(v) => setSite({ landmark: v })} /></div>
      <div className="label">शहर</div>
      <div className="field">
        <select value={site.city} onChange={(e) => setSite({ city: e.target.value, zone: e.target.value === 'अन्य' ? null : 'I', zone_confirmed: false })}>
          {CITIES.map((c) => <option key={c}>{c}</option>)}
        </select>
        <ChevronDown size={22} color="var(--text-2)" />
      </div>

      <div className="card ask" style={{ marginTop: 14, padding: 14 }}>
        <div className="ask-card" style={{ padding: 0 }}>
          <div className="grow">
            {site.zone ? <div className="title">{ZONE_TEXT[site.zone]}</div> : <div className="title">ज़ोन चुनें</div>}
            <div className="sub">{suggested ? 'शहर से सुझाया गया' : 'साथी या यूनियन से पूछें'}</div>
          </div>
          <button className={`chip ${site.zone_confirmed ? 'ok' : 'ask'}`} disabled={!site.zone}
            onClick={() => setSite({ zone_confirmed: !site.zone_confirmed })}>
            {site.zone_confirmed ? <><Check size={16} /> पक्का</> : <><CircleHelp size={16} /> पक्का करें</>}
          </button>
        </div>
        <div className="toggle-chips" style={{ marginTop: 10, flexWrap: 'nowrap' }}>
          {['I', 'II', 'III'].map((z) => (
            <button key={z} className={`tchip ${site.zone === z ? 'on' : ''}`} style={{ flex: 1, minHeight: 40, padding: 0 }}
              onClick={() => setSite({ zone: z, zone_confirmed: false })}>ज़ोन {z}</button>
          ))}
        </div>
        <Need msg={req.show('zone')} />
      </div>

      <div className="card pad" style={{ marginTop: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 16.5 }}>क्या यह रेलवे, केंद्र सरकार की कंपनी, एयरपोर्ट, बंदरगाह या खदान का काम है?</div>
        <div className="toggle-chips" style={{ marginTop: 12, flexWrap: 'nowrap' }}>
          {[['central', 'हाँ'], ['state', 'नहीं'], ['unknown', 'पता नहीं']].map(([v, t]) => (
            <button key={v} className={`tchip ${site.sphere === v ? 'on' : ''}`} style={{ flex: 1, padding: 0 }} onClick={() => setSite({ sphere: v })}>{t}</button>
          ))}
        </div>
        <Need msg={req.show('sphere')} />
      </div>

      {/* Composed (not in UI/): GPS opt-in, BUILD_PLAN rule 7 — ask, show the coordinates, store with the site. */}
      <div className="card pad" style={{ marginTop: 12 }}>
        <div className="row">
          <span className="icon-bubble cream"><MapPin size={18} /></span>
          <div className="grow">
            <div style={{ fontWeight: 700, fontSize: 16.5 }}>साइट की GPS जगह जोड़ें?</div>
            <div className="small" style={{ color: 'var(--text-2)' }}>आपकी मर्ज़ी — रोज़ की एंट्री के साथ जगह भी सेव होगी</div>
          </div>
        </div>
        {d.gps_opt_in && d.gps ? (
          <div className="row between" style={{ marginTop: 10 }}>
            <span className="gps-chip"><MapPin size={16} /> {d.gps.lat.toFixed(5)}, {d.gps.lon.toFixed(5)} · ±{d.gps.acc} मी</span>
            <button className="link" onClick={() => up({ gps: null, gps_opt_in: false })}>हटाएँ</button>
          </div>
        ) : (
          <div className="toggle-chips" style={{ marginTop: 12, flexWrap: 'nowrap' }}>
            <button className="tchip" style={{ flex: 1, padding: 0 }} onClick={addGps} disabled={locating}>{locating ? 'ढूँढ रहे हैं…' : 'हाँ, जगह जोड़ें'}</button>
            <button className={`tchip ${!d.gps_opt_in ? 'on' : ''}`} style={{ flex: 1, padding: 0 }} onClick={() => up({ gps: null, gps_opt_in: false })}>नहीं</button>
          </div>
        )}
      </div>

      <div className="bottom-actions">
        <Btn icon={ArrowRight} onClick={req.go}>आगे बढ़ें</Btn>
      </div>
    </div>
  )
}

const START_HOURS = [6, 7, 8, 9, 10, 11]
const END_HOURS = [4, 5, 6, 7, 8, 9]
const BREAKS = [[0, 'कोई नहीं'], [30, 'आधा घंटा'], [45, '45 मिनट'], [60, '1 घंटा'], [90, 'डेढ़ घंटा']]
const PERIODS = [['daily', 'रोज़'], ['weekly', 'हफ़्ते'], ['fortnightly', '15 दिन'], ['monthly', 'महीने']]

function Contractor({ d, up, back, progress, finish }) {
  const [busy, setBusy] = useState(false)
  const t = d.thekedar
  const setT = (patch) => up({ thekedar: { ...t, ...patch } })
  const startH = Number(d.usual.start.slice(0, 2))
  const endH = Number(d.usual.end.slice(0, 2)) - 12
  const digits = t.phone.replace(/\D/g, '')
  const wage = Number(d.agreed_daily)
  const req = useRequired({
    name: !NAME_OK(t.name) && 'ठेकेदार का नाम लिखें',
    phone: !t.phone_unknown && !/^(91)?[6-9]\d{9}$/.test(digits) && (digits ? '10 अंकों का सही नंबर डालें' : 'नंबर डालें, या ‘पता नहीं’ दबाएँ'),
    wage: !(wage >= 100 && wage <= 5000) && (d.agreed_daily ? '₹100 से ₹5000 के बीच लिखें' : 'रोज़ की तय मज़दूरी लिखें'),
  }, async () => { setBusy(true); await finish() })
  return (
    <div className="screen">
      <TopBar onBack={back} progress={{ ...progress, step: 7 }} speakText="ठेकेदार और मज़दूरी। जो पता हो वही भरें" />
      <h1 className="title">ठेकेदार और मज़दूरी</h1>
      <p className="subtitle">जो पता हो वही भरें, बाकी ‘पता नहीं’ रहने दें</p>
      <div className="label" style={{ marginTop: 0 }}>ठेकेदार का नाम</div>
      <div className={`field ${req.show('name') ? 'invalid' : ''}`}><input value={t.name} onChange={(e) => setT({ name: e.target.value })} placeholder="जैसे: कैलाश" maxLength={40} /><VoiceInput field="name" language={d.language} keepAudio={d.consent_keep_audio} onText={(v) => setT({ name: v })} /></div>
      <Need msg={req.show('name')} />
      <div className="label">ठेकेदार का फ़ोन</div>
      <div className={`field ${req.show('phone') ? 'invalid' : ''}`}>
        <input inputMode="tel" value={t.phone} disabled={t.phone_unknown} onChange={(e) => setT({ phone: e.target.value.replace(/[^\d+ ]/g, '') })} placeholder="नंबर डालें" />
        <button className={`pill-btn ${t.phone_unknown ? 'on' : ''}`} onClick={() => setT({ phone_unknown: !t.phone_unknown, phone: '' })}>पता नहीं</button>
      </div>
      <Need msg={req.show('phone')} />
      <div className="two-col">
        <div>
          <div className="label">रोज़ का समय</div>
          <div className="field" style={{ gap: 4, padding: '0 10px' }}>
            <select aria-label="शुरू" value={startH} onChange={(e) => up({ usual: { ...d.usual, start: `${String(e.target.value).padStart(2, '0')}:00` } })}>
              {START_HOURS.map((h) => <option key={h} value={h}>सुबह {h}</option>)}
            </select>
            <span>–</span>
            <select aria-label="ख़त्म" value={endH} onChange={(e) => up({ usual: { ...d.usual, end: `${Number(e.target.value) + 12}:00` } })}>
              {END_HOURS.map((h) => <option key={h} value={h}>शाम {h}</option>)}
            </select>
          </div>
        </div>
        <div>
          <div className="label">आराम</div>
          <div className="field" style={{ padding: '0 10px' }}>
            <select value={d.usual.break_min} onChange={(e) => up({ usual: { ...d.usual, break_min: Number(e.target.value) } })}>
              {BREAKS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
        </div>
      </div>
      <div className="label">तय मज़दूरी</div>
      <div className={`field ${req.show('wage') ? 'invalid' : ''}`}>
        <span style={{ fontWeight: 700, fontSize: 17 }}>₹</span>
        <input inputMode="numeric" value={d.agreed_daily} onChange={(e) => up({ agreed_daily: e.target.value.replace(/\D/g, '').slice(0, 5) })} placeholder="600" />
        <span style={{ fontWeight: 700 }}>/ दिन</span>
        <Pencil size={20} color="var(--text-2)" />
      </div>
      <Need msg={req.show('wage')} />
      <div className="label">पैसा कब मिलता है?</div>
      <div className="toggle-chips" style={{ flexWrap: 'nowrap' }}>
        {PERIODS.map(([v, l]) => (
          <button key={v} className={`tchip ${d.wage_period === v ? 'on' : ''}`} style={{ flex: 1, padding: 0 }} onClick={() => up({ wage_period: v })}>{l}</button>
        ))}
      </div>
      <div className="row small" style={{ marginTop: 12 }}><Info size={18} /> ये बातें बाद में भी बदल सकते हैं</div>
      <div className="bottom-actions">
        <Btn icon={Check} disabled={busy} onClick={req.go}>हो गया — हिसाब शुरू करें</Btn>
      </div>
    </div>
  )
}
