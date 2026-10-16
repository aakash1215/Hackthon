import { useCallback, useEffect, useMemo, useState } from 'react'
import { AppCtx } from './components/Ui.jsx'
import { clearPhone, getJobs, getProfile, saveProfile } from './lib/db.js'
import { apiJson } from './lib/api.js'
import { startSync, subscribe } from './lib/sync.js'
import { loadDemoFromUrl } from './lib/demo.js'
import Onboarding from './screens/Onboarding.jsx'
import Home from './screens/Home.jsx'
import Record from './screens/Record.jsx'
import Saved from './screens/Saved.jsx'
import Confirm from './screens/Confirm.jsx'
import Ledger from './screens/Ledger.jsx'
import Hisaab from './screens/Hisaab.jsx'
import FileTab from './screens/FileTab.jsx'
import Settings from './screens/Settings.jsx'
import Later from './screens/Later.jsx'
import HisaabCheck from './screens/HisaabCheck.jsx'
import RecordOther from './screens/RecordOther.jsx'
import Diff from './screens/Diff.jsx'
import Telegram from './screens/Telegram.jsx'
import PromiseScreen from './screens/Promise.jsx'
import Stopped from './screens/Stopped.jsx'
import Agent from './screens/Agent.jsx'
import { setEngine } from './lib/engine.js'

const SCREENS = { home: Home, record: Record, saved: Saved, confirm: Confirm, ledger: Ledger, hisaab: Hisaab, file: FileTab, settings: Settings, later: Later,
  hisaabCheck: HisaabCheck, recordOther: RecordOther, diff: Diff, telegram: Telegram, promise: PromiseScreen, stopped: Stopped, agent: Agent }

// The account was removed on the hub (reset / deleted): log this phone out instead of failing every call.
// Not while the phone still has queued uploads: an offline sign-up reaches the hub only when those run.
async function checkAccount(p) {
  try {
    await apiJson('GET', `/api/workers/${encodeURIComponent(p.worker_id)}`, null, { timeoutMs: 8000 })
  } catch (e) {
    // Failed jobs (4xx, e.g. uploads for this missing account) never retry, so they must not keep it logged in.
    if (e.code !== 'WORKER_NOT_FOUND' || (await getJobs()).some((j) => !j.failed)) return
    await clearPhone()
    window.location.replace('/')
  }
}

export default function App() {
  const [profile, setProfileState] = useState(undefined) // undefined = loading
  const [stack, setStack] = useState([{ name: 'home', params: {} }])
  const [sync, setSync] = useState({})
  const [toastMsg, setToastMsg] = useState(null)

  useEffect(() => {
    // ?demo=<worker_id> loads the seeded demo persona first (P6); a failure leaves the phone as it was.
    loadDemoFromUrl().catch(() => false).finally(() => {
      getProfile().then((p) => { setEngine(p?.ai_engine); setProfileState(p || null); if (p) checkAccount(p) })
        .catch(() => setProfileState(null))
      startSync()
    })
    return subscribe(setSync)
  }, [])

  const toast = useCallback((msg) => {
    setToastMsg(msg)
    setTimeout(() => setToastMsg(null), 3200)
  }, [])

  const setProfile = useCallback(async (p) => {
    await saveProfile(p)
    setEngine(p?.ai_engine)
    setProfileState(p)
  }, [])

  const nav = useMemo(() => ({
    go: (name, params = {}) => { setStack((s) => [...s, { name, params }]); window.scrollTo(0, 0) },
    back: () => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s)),
    reset: (name, params = {}) => { setStack([{ name, params }]); window.scrollTo(0, 0) },
    replace: (name, params = {}) => setStack((s) => [...s.slice(0, -1), { name, params }]),
  }), [])

  const ctx = { ...nav, profile, setProfile, sync, toast }

  let body
  if (profile === undefined) body = null
  else if (!profile || !profile.onboarded) body = <Onboarding />
  else {
    const top = stack[stack.length - 1]
    const Screen = SCREENS[top.name] || Home
    body = <Screen key={stack.length + top.name} {...top.params} />
  }

  return (
    <AppCtx.Provider value={ctx}>
      {body}
      {toastMsg && <div className="toast" role="status">{toastMsg}</div>}
    </AppCtx.Provider>
  )
}
