// 4-digit PIN dots + keypad (UI/ O4 and A1). Calls onDone(pin) when the 4th digit is entered.
import { useEffect, useState } from 'react'
import { Delete } from 'lucide-react'

export default function PinPad({ onDone, resetKey, error, leftSlot = null, disabled = false }) {
  const [pin, setPin] = useState('')
  useEffect(() => { setPin('') }, [resetKey])

  function press(d) {
    if (disabled || pin.length >= 4) return
    const n = pin + d
    setPin(n)
    if (n.length === 4) setTimeout(() => onDone(n), 120)
  }

  return (
    <div className="pinpad">
      <div className={`pin-dots ${error ? 'shake' : ''}`} aria-label={`${pin.length} अंक डाले`}>
        {[0, 1, 2, 3].map((i) => <span key={i} className={i < pin.length ? 'on' : ''} />)}
      </div>
      <div className="pin-keys">
        {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((k) => (
          <button key={k} className="pin-key" onClick={() => press(k)} disabled={disabled}>{k}</button>
        ))}
        <div className="pin-left">{leftSlot}</div>
        <button className="pin-key" onClick={() => press('0')} disabled={disabled}>0</button>
        <button className="pin-key back" onClick={() => setPin((p) => p.slice(0, -1))} aria-label="मिटाएँ" disabled={disabled}>
          <Delete size={30} />
        </button>
      </div>
    </div>
  )
}
