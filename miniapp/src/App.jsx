import React, { useState, useEffect, createContext, useContext } from 'react'
import BottomNav from './components/BottomNav'
import Dashboard from './pages/Dashboard'
import QuestPage from './pages/QuestPage'
import Leaderboard from './pages/Leaderboard'
import PrizeShop from './pages/PrizeShop'
import HistoryPage from './pages/HistoryPage'
import Spinner from './components/Spinner'
import { authInit } from './api'

export const AppCtx = createContext(null)
export const useApp = () => useContext(AppCtx)

const PAGES = {
  home: Dashboard,
  quest: QuestPage,
  board: Leaderboard,
  shop: PrizeShop,
  history: HistoryPage,
}

export default function App() {
  const [tab, setTab] = useState('home')
  const [player, setPlayer] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    tg?.ready()
    tg?.expand()

    const user = tg?.initDataUnsafe?.user || {
      id: 999999999,
      first_name: 'Dev',
      last_name: 'User',
      username: 'devuser',
    }

    authInit(user)
      .then((data) => setPlayer(data))
      .catch(() => setError('Не вдалось підключитись до сервера. Спробуй пізніше.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="splash">
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
        <div style={{ fontSize: 48 }}>🏆</div>
        <Spinner />
      </div>
    </div>
  )

  if (error) return (
    <div className="error-screen">
      <div style={{ fontSize: 40 }}>⚠️</div>
      <p>{error}</p>
    </div>
  )

  const Page = PAGES[tab]

  return (
    <AppCtx.Provider value={{ player, setPlayer, showToast, setTab }}>
      <div className="app">
        <Page />
        <BottomNav active={tab} onChange={setTab} />
      </div>
      {toast && <div className="toast">{toast}</div>}
    </AppCtx.Provider>
  )
}
