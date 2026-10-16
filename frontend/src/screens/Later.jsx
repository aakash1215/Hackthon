// Placeholder for flows that land in later phases (thekedar hisaab check P3, Telegram P4).
import { Clock } from 'lucide-react'
import { Btn, TopBar, useApp } from '../components/Ui.jsx'

export default function Later({ title = 'जल्द आ रहा है' }) {
  const { back } = useApp()
  return (
    <div className="screen">
      <TopBar title={title} onBack={back} speakText={`${title}। यह सुविधा जल्द आ रही है।`} />
      <div className="big-check"><span><Clock size={30} /></span></div>
      <h1 className="saved-title">जल्द आ रहा है</h1>
      <p className="center muted">यह हिस्सा अगले चरण में जुड़ेगा। तब तक रोज़ का काम और पैसा बोलकर दर्ज करते रहें।</p>
      <div className="bottom-actions"><Btn onClick={back}>ठीक है</Btn></div>
    </div>
  )
}
