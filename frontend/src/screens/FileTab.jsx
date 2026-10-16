// केस फ़ाइल (UI/ F1): readiness ring + checklist from the hub's coach, period + redaction, and the
// evidence-file export (PDF + bundle). PIN is cut for this build (BUILD_PLAN §4), so the button keeps
// F1's lock icon without the word PIN. Result card and site-board sheet are composed in the same style.
import { useEffect, useRef, useState } from 'react'
import {
  Banknote, Camera, Check, ChevronRight, CircleAlert, FileDown, FileText, Link2, Lock, Mic, Plus, Scale, Settings as Cog, Share2,
} from 'lucide-react'
import { Btn, Sheet, Spinner, TabBar, TopBar, useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'
import { read, write } from '../lib/db.js'
import { localIso, monthName, todayIso } from '../lib/format.js'
import { shortCode } from '../lib/hash.js'
import { queueJson, savePhoto } from '../lib/sync.js'

const ACTIONS = {
  thekedar_phone: { icon: Plus, label: 'जोड़ें' },
  site_board: { icon: Camera, label: 'फ़ोटो' },
  coworker: { icon: Mic, label: 'रिकॉर्ड' },
  record_day: { icon: Mic, label: 'बोलें' },
  payment: { icon: Banknote, label: 'जोड़ें' },
  hisaab_check: { icon: Scale, label: 'जाँचें' },
}
const SHOW_MAX = 6

function Ring({ done, total }) {
  const r = 38
  const c = 2 * Math.PI * r
  const frac = total ? Math.min(1, done / total) : 0
  return (
    <div className="ring" aria-label={`${done}/${total}`}>
      <svg width="92" height="92" viewBox="0 0 92 92">
        <circle cx="46" cy="46" r={r} fill="none" stroke="var(--surface)" strokeWidth="10" />
        <circle cx="46" cy="46" r={r} fill="none" stroke="var(--brand)" strokeWidth="10" strokeDasharray={`${c * frac} ${c}`} />
      </svg>
      <div className="n">{done}/{total}</div>
    </div>
  )
}

export default function FileTab() {
  const { profile, go, toast } = useApp()
  const [coach, setCoach] = useState(null)
  const [showAll, setShowAll] = useState(false)
  const [redact, setRedact] = useState(true)
  const [exp, setExp] = useState({ state: 'idle' }) // idle | running | done | error
  const [board, setBoard] = useState(null) // { builder, rera } while the site-board sheet is open
  const fileRef = useRef(null)
  const today = todayIso()
  const from = `${today.slice(0, 8)}01`
  const period = `${Number(from.slice(8))}–${Number(today.slice(8))} ${monthName(Number(today.slice(5, 7)) - 1)}`

  const load = () => {
    api.coach(profile.worker_id).then((c) => { setCoach(c); write('cache:coach', c) }).catch(() => {})
  }
  useEffect(() => {
    read('cache:coach').then((c) => c && setCoach((cur) => cur || c))
    load()
  }, [profile.worker_id])

  function onAction(action) {
    if (action === 'thekedar_phone') go('settings')
    else if (action === 'site_board') fileRef.current?.click()
    else if (action === 'coworker') go('recordOther', { who: 'coworker' })
    else if (action === 'hisaab_check') go('hisaabCheck')
    else if (action === 'record_day') go('record', { kind: 'workday' })
    else if (action === 'payment') go('record', { kind: 'payment' })
  }

  async function onBoardPhoto(e) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    try {
      const r = await savePhoto({ workerId: profile.worker_id, kind: 'site_board', photo: f, clientTs: localIso() })
      toast(`फ़ोटो सेव ✓ #${shortCode(r.sha256, 2)}`)
      setBoard({ builder: '', rera: '' })
    } catch {
      toast('फ़ोटो सेव नहीं हो पाई — फिर कोशिश करें')
    }
  }

  async function saveBoard(skip) {
    const b = board
    setBoard(null)
    if (!b) return
    if (!skip && (b.builder.trim() || b.rera.trim())) {
      await queueJson('POST', '/api/sites/board', { worker_id: profile.worker_id, principal_employer: b.builder.trim() || null, maharera_no: b.rera.trim() || null })
      toast('साइट की जानकारी सेव हो गई')
    }
    setTimeout(load, 1500)
  }

  async function makePdf() {
    setExp({ state: 'running' })
    try {
      const r = await api.exportPacket({ worker_id: profile.worker_id, date_from: from, date_to: today, redact_witness_names: redact })
      setExp({ state: 'done', r })
    } catch (e) {
      setExp({ state: 'error', code: e instanceof api.NetworkError ? 'NETWORK' : e.code })
    }
  }

  async function sharePdf() {
    const r = exp.r
    const url = r.pdf_url || r.html_url
    try {
      if (r.pdf_url && navigator.canShare) {
        const blob = await (await fetch(r.pdf_url)).blob()
        const file = new File([blob], 'apna-hisaab-evidence-file.pdf', { type: 'application/pdf' })
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({ files: [file], title: 'अपना हिसाब — केस फ़ाइल' })
          return
        }
      }
    } catch (e) {
      if (e?.name === 'AbortError') return
    }
    window.open(url, '_blank', 'noopener')
  }

  const items = coach?.items || []
  const todo = items.filter((i) => !i.ok)
  const done = items.filter((i) => i.ok)
  const doneShown = showAll ? done : done.slice(0, Math.max(1, SHOW_MAX - todo.length))
  const hidden = done.length - doneShown.length
  const total = coach?.total || 12
  const nDone = coach?.done ?? done.length
  const chain = exp.r?.chain_head
  const chainShort = typeof chain === 'string' ? shortCode(chain) : chain?.short || ''

  return (
    <div className="screen with-tabs">
      <TopBar title="केस फ़ाइल" speakText={`केस फ़ाइल। ${nDone} में से ${total} तैयार। यह क़ानूनी स्कोर नहीं है।`} />

      <div className="card ring-card" style={{ marginTop: 6 }}>
        <Ring done={nDone} total={total} />
        <div className="grow">
          <div className="h">{nDone}/{total} तैयार</div>
          {total - nDone > 0 && <div className="s">{total - nDone} चीज़ें और जोड़ें तो फ़ाइल मज़बूत बनेगी</div>}
          <div className="x">यह क़ानूनी स्कोर नहीं है</div>
        </div>
      </div>

      <div className="card checklist">
        {!coach && <div className="row" style={{ minHeight: 56 }}><Spinner /> हब से जुड़ने पर दिखेगा</div>}
        {todo.map((it) => {
          const a = ACTIONS[it.action]
          return (
            <div key={it.id} className="crow todo">
              <CircleAlert size={24} color="var(--ask)" style={{ flex: 'none' }} />
              <div className="t">
                <span className="lbl">{it.label_hi}</span>
                {a && <button className="pill-act" onClick={() => onAction(it.action)}><a.icon size={16} /> {a.label}</button>}
              </div>
            </div>
          )
        })}
        {doneShown.map((it) => (
          <div key={it.id} className="crow done">
            <span className="tick-dot"><Check size={15} strokeWidth={3} /></span>
            <div className="t"><span className="lbl">{it.label_hi}</span></div>
          </div>
        ))}
        {hidden > 0 && <button className="more-row" onClick={() => setShowAll(true)}>+ {hidden} और पूरे</button>}
      </div>
      <input ref={fileRef} className="hidden-input" type="file" accept="image/*" capture="environment" onChange={onBoardPhoto} />

      <div className="card opts">
        <div className="orow"><span>अवधि</span><span className="period">{period}</span></div>
        <div className="orow">
          <span>गवाहों के नाम छिपाएँ</span>
          <button className={`switch ${redact ? 'on' : ''}`} role="switch" aria-checked={redact} aria-label="गवाहों के नाम छिपाएँ" onClick={() => setRedact((v) => !v)} />
        </div>
      </div>

      <Btn className="big" icon={exp.state === 'running' ? null : Lock} onClick={makePdf} disabled={exp.state === 'running'}>
        {exp.state === 'running' ? <><Spinner /> फ़ाइल बन रही है…</> : 'PDF बनाएँ'}
      </Btn>
      {exp.state === 'error' && <div className="info-row" style={{ marginTop: 10, color: 'var(--urgent)' }}><CircleAlert size={20} /> फ़ाइल नहीं बन पाई ({exp.code}) — हब से जुड़कर फिर कोशिश करें।</div>}

      {exp.state === 'done' && (
        <div className="card pad stack" style={{ marginTop: 12 }}>
          <div className="row"><span className="tick-dot"><Check size={15} strokeWidth={3} /></span><b>फ़ाइल तैयार</b></div>
          {!exp.r.pdf_url && <div className="small" style={{ color: 'var(--ask)' }}>PDF नहीं बन पाई — पेज खोलकर प्रिंट करके PDF सेव करें</div>}
          <a className="btn primary" href={exp.r.pdf_url || exp.r.html_url} target="_blank" rel="noopener noreferrer"><FileText size={22} /> {exp.r.pdf_url ? 'PDF खोलें' : 'फ़ाइल खोलें'}</a>
          <Btn variant="outline" icon={Share2} onClick={sharePdf}>शेयर करें</Btn>
          {exp.r.zip_url && <a className="btn plain" href={exp.r.zip_url} download><FileDown size={22} /> पूरा बंडल (.zip)</a>}
          {chainShort && <div className="row small" style={{ color: 'var(--text-2)' }}><Link2 size={16} /> रिकॉर्ड कोड {chainShort}</div>}
        </div>
      )}
      <p className="foot">आपके अपने रिकॉर्ड से बना — क़ानूनी सबूत की गारंटी नहीं।</p>

      <div className="card" style={{ marginTop: 4 }}>
        <button className="settings-row" onClick={() => go('settings')}>
          <span className="icon-bubble"><Cog size={20} /></span>
          <div className="grow"><div className="t">सेटिंग्स और सुरक्षा</div><div className="d">रिकॉर्ड की जाँच, भेजना बाकी, मंज़ूरी</div></div>
          <ChevronRight size={22} color="var(--text-2)" />
        </button>
      </div>

      <Sheet open={!!board} onClose={() => saveBoard(true)}>
        {board && (
          <>
            <h2>साइट बोर्ड पर क्या लिखा है?</h2>
            <p className="muted" style={{ marginTop: 0 }}>चाहें तो भरें — न पता हो तो छोड़ दें</p>
            <div className="label">बिल्डर / कंपनी का नाम</div>
            <div className="field"><input value={board.builder} maxLength={120} onChange={(e) => setBoard({ ...board, builder: e.target.value })} /></div>
            <div className="label">MahaRERA नंबर</div>
            <div className="field"><input value={board.rera} maxLength={40} onChange={(e) => setBoard({ ...board, rera: e.target.value.toUpperCase() })} placeholder="P5…" /></div>
            <div className="btn-row" style={{ marginTop: 16 }}>
              <Btn variant="plain" className="narrow" onClick={() => saveBoard(true)}>छोड़ें</Btn>
              <Btn icon={Check} onClick={() => saveBoard(false)}>सेव करें</Btn>
            </div>
          </>
        )}
      </Sheet>
      <TabBar active="file" />
    </div>
  )
}
