// Thin component layer for the UI/ clone. Icons are lucide-react (bundled, no CDN).
import { createContext, useContext } from 'react'
import {
  ArrowLeft, Bot, CalendarCheck, Check, CircleAlert, CircleHelp, FileText, House, IndianRupee, Volume2, X,
} from 'lucide-react'
import { speak } from '../lib/device.js'

export const AppCtx = createContext(null)
export const useApp = () => useContext(AppCtx)

export function TopBar({ title, onBack, onCancel, progress, speakText, right }) {
  const { toast } = useApp()
  const listen = () => {
    if (!speak(speakText || title || '')) toast('इस फ़ोन में पढ़कर सुनाने वाली आवाज़ नहीं मिली')
  }
  return (
    <div className="topbar">
      {onBack && (
        <button className="back" onClick={onBack} aria-label="पीछे">
          <ArrowLeft size={26} />
        </button>
      )}
      {onCancel && (
        <button className="cancel" onClick={onCancel}>
          <X size={26} color="var(--text)" /> रद्द करें
        </button>
      )}
      {progress && (
        <div className="progress" aria-label={`चरण ${progress.step}/${progress.total}`}>
          {Array.from({ length: progress.total }, (_, i) => <span key={i} className={i < progress.step ? 'on' : ''} />)}
        </div>
      )}
      {title && !progress && <div className="title">{title}</div>}
      {right}
      {speakText !== false && (
        <button className="listen" onClick={listen}>
          <Volume2 size={20} /> सुनें
        </button>
      )}
    </div>
  )
}

export function Btn({ variant = 'primary', icon: Icon, children, className = '', ...rest }) {
  return (
    <button className={`btn ${variant} ${className}`} {...rest}>
      {Icon && <Icon size={22} strokeWidth={2.4} />}
      {children}
    </button>
  )
}

const STATUS = {
  green: { cls: 'ok', icon: Check, text: 'ठीक' },
  amber: { cls: 'ask', icon: CircleHelp, text: 'पक्का करें' },
  red: { cls: 'urgent', icon: CircleAlert, text: 'बताना ज़रूरी' },
}
export function StatusChip({ status }) {
  const s = STATUS[status]
  if (!s) return null
  const I = s.icon
  return (
    <span className={`chip ${s.cls}`}>
      <I size={17} strokeWidth={2.4} /> {s.text}
    </span>
  )
}

export function Sheet({ open, onClose, children }) {
  if (!open) return null
  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()} role="dialog">
        <div className="handle" />
        {children}
      </div>
    </div>
  )
}

const TABS = [
  { id: 'home', label: 'आज', icon: House },
  { id: 'ledger', label: 'खाता', icon: CalendarCheck },
  { id: 'hisaab', label: 'हिसाब', icon: IndianRupee },
  { id: 'file', label: 'फ़ाइल', icon: FileText },
  { id: 'agent', label: 'सहायक', icon: Bot },
]
export function TabBar({ active }) {
  const { reset } = useApp()
  return (
    <nav className="tabbar">
      {TABS.map((t) => {
        const I = t.icon
        return (
          <button key={t.id} className={active === t.id ? 'on' : ''} onClick={() => reset(t.id)}>
            <span className="ic"><I size={24} /></span>
            {t.label}
          </button>
        )
      })}
    </nav>
  )
}

export function Spinner() {
  return <span className="spinner" aria-label="लोड हो रहा है" />
}
