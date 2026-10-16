import { useEffect, useState } from 'react'

// P0 placeholder: shows hub health. P2 replaces this with the screens cloned from UI/.
export default function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)))
  }, [])

  return (
    <main>
      <h1>अपना हिसाब</h1>
      {error && <p>Hub not reachable: {error}</p>}
      {health ? <pre>{JSON.stringify(health, null, 2)}</pre> : !error && <p>…</p>}
    </main>
  )
}
