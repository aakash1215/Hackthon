// Display formatting only. Amounts shown here come from the hub's wage engine; nothing is computed
// on the phone except the hours summary on the confirm card (subtraction of worker-confirmed times).

export function localIso(d = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  const off = -d.getTimezoneOffset()
  const sign = off >= 0 ? '+' : '-'
  const oh = pad(Math.floor(Math.abs(off) / 60))
  const om = pad(Math.abs(off) % 60)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${sign}${oh}:${om}`
}
export const todayIso = () => localIso().slice(0, 10)
export function addDays(iso, n) {
  const d = new Date(`${iso}T12:00:00`)
  d.setDate(d.getDate() + n)
  return localIso(d).slice(0, 10)
}

const MONTHS = ['जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर']
const WEEKDAYS = ['रविवार', 'सोमवार', 'मंगलवार', 'बुधवार', 'गुरुवार', 'शुक्रवार', 'शनिवार']
const WD_SHORT = ['रवि', 'सोम', 'मंगल', 'बुध', 'गुरु', 'शुक्र', 'शनि']
export const WD_LETTER = ['सो', 'मं', 'बु', 'गु', 'शु', 'श', 'र'] // Monday-first calendar header

const asDate = (iso) => new Date(`${iso}T12:00:00`)
export const monthName = (m) => MONTHS[m]
export const dayMonth = (iso) => { const d = asDate(iso); return `${d.getDate()} ${MONTHS[d.getMonth()]}` }
export const longDate = (iso) => { const d = asDate(iso); return `${WEEKDAYS[d.getDay()]}, ${d.getDate()} ${MONTHS[d.getMonth()]}` }
export const shortDayDate = (iso) => { const d = asDate(iso); return `${WD_SHORT[d.getDay()]}, ${d.getDate()} ${MONTHS[d.getMonth()]}` }
export const weekdayShort = (iso) => WD_SHORT[asDate(iso).getDay()]

export function rupees(v, { decimals = false } = {}) {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return '₹' + n.toLocaleString('en-IN', decimals ? { minimumFractionDigits: 2, maximumFractionDigits: 2 } : { maximumFractionDigits: 0 })
}

export const toMin = (hhmm) => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m }

/** "09:00" → "9:00" (12-hour face, as in UI/ "9:00 – 7:00"). */
export function clock12(hhmm) {
  if (!hhmm) return '—'
  const [h, m] = hhmm.split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')}`
}
export function partOfDay(hhmm) {
  const h = Number(hhmm.split(':')[0])
  if (h < 12) return 'सुबह'
  if (h < 16) return 'दोपहर'
  if (h < 20) return 'शाम'
  return 'रात'
}
export const clockLong = (hhmm) => (hhmm ? `${partOfDay(hhmm)} ${clock12(hhmm)}` : '—')

/** Worked minutes from worker-confirmed start/end/break (display only). */
export function workedMinutes(start, end, breakMin = 0) {
  if (!start || !end) return null
  let span = toMin(end) - toMin(start)
  if (span <= 0) span += 24 * 60
  return Math.max(0, span - (Number(breakMin) || 0))
}
export function hoursText(mins) {
  if (mins == null) return ''
  const h = mins / 60
  return `${Number.isInteger(h) ? h : h.toFixed(1)} घंटे`
}

export function monthRange(year, month) {
  const pad = (n) => String(n).padStart(2, '0')
  const last = new Date(year, month + 1, 0).getDate()
  return [`${year}-${pad(month + 1)}-01`, `${year}-${pad(month + 1)}-${pad(last)}`]
}

/** Monday-first week containing iso. */
export function weekOf(iso) {
  const d = asDate(iso)
  const dow = (d.getDay() + 6) % 7
  return Array.from({ length: 7 }, (_, i) => addDays(iso, i - dow))
}
