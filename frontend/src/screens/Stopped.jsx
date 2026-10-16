// बातचीत रोक दी गई (UI/ S8 clone). Shown when the thekedar's message was hostile: the bot did not
// reply and will not (BUILD_PLAN §7). The message itself is saved with its SHA-256.
import { Phone, Scale, ShieldAlert, Siren, Users } from 'lucide-react'
import { useApp } from '../components/Ui.jsx'
import * as api from '../lib/api.js'

function code8(hex) {
  if (!hex) return null
  const h = hex.toUpperCase()
  return `${h.slice(0, 4)}-${h.slice(4, 8)}`
}

function CallCard({ icon: I, title, desc, href, onClick, red }) {
  const inner = (
    <>
      <span className={`icon-bubble ${red ? 'red' : ''}`}><I size={20} /></span>
      <div className="grow"><div className="t">{title}</div><div className="d">{desc}</div></div>
      <span className={`call-btn ${red ? 'red' : ''}`}><Phone size={22} fill="currentColor" /></span>
    </>
  )
  return href
    ? <a className="card call-card" href={href}>{inner}</a>
    : <button className="card call-card" onClick={onClick}>{inner}</button>
}

export default function Stopped({ item }) {
  const { profile, go, reset } = useApp()
  const code = code8(item?.message_sha256)
  const union = profile.union_phone

  async function home() {
    if (item?.id) await api.inboxAction(item.id, { action: 'seen' }).catch(() => {})
    reset('home')
  }

  return (
    <div className="screen">
      <div className="stop-hero">
        <div className="shield-ring"><ShieldAlert size={44} fill="var(--urgent)" stroke="#fff" strokeWidth={1.8} /></div>
        <h1>बातचीत रोक दी गई</h1>
        <p>आप सुरक्षित रहें। बहस न करें, वहाँ से हट जाएँ।</p>
        <div className="code-pill">संदेश सेव{code ? ` · कोड ${code}` : ''}</div>
      </div>

      <div className="label" style={{ color: 'var(--text)', fontSize: 16, margin: '18px 0 10px' }}>अभी बात करें:</div>
      <CallCard icon={Scale} title="विधिक सहायता (मुफ़्त)" desc="NALSA हेल्पलाइन 15100" href="tel:15100" />
      <CallCard icon={Users} title="यूनियन / सहायक" desc={union ? `आपका सेव किया नंबर · ${union}` : 'नंबर सेव नहीं — सेटिंग्स में जोड़ें'}
        href={union ? `tel:${union}` : undefined} onClick={union ? undefined : () => go('settings')} />
      <CallCard icon={Siren} title="आपातकाल" desc="पुलिस 112" href="tel:112" red />

      <p className="foot">ऐप ने कोई जवाब नहीं दिया और न देगा।</p>
      <div className="bottom-actions">
        <button className="btn plain" style={{ minHeight: 'var(--btn-h)' }} onClick={home}>होम पर जाएँ</button>
      </div>
    </div>
  )
}
