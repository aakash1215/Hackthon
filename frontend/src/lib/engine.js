// Which AI engine this phone asks the hub for: 'local' (open-weight models on the hub, free, default) or
// 'cloud' (optional ChatGPT API: faster, costs money, needs internet). Set from the profile by App.jsx.
let current = 'local'

export const getEngine = () => current
export function setEngine(e) {
  current = e === 'cloud' ? 'cloud' : 'local'
}
