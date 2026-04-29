const BASE = import.meta.env.VITE_API_URL || ''

let _token = null
export const setToken = (t) => { _token = t }
export const getToken = () => _token

async function req(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' }
  if (_token) headers['Authorization'] = `Bearer ${_token}`

  const opts = { method, headers }

  if (body instanceof FormData) {
    delete headers['Content-Type']
    opts.body = body
  } else if (body) {
    opts.body = JSON.stringify(body)
  }

  const res = await fetch(`${BASE}${path}`, opts)

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

// ============================================================
// AUTH
// ============================================================
export const signIn = (initData) =>
  req('POST', '/auth/signin', { init_data: initData })

/**
 * authInit — викликається при старті MiniApp.
 * Повертає об'єкт у формі PlayerProfile (не raw AuthResponse),
 * щоб App.jsx та Dashboard.jsx працювали з одним контрактом.
 */
export const authInit = async (tgUser) => {
  const tg = window.Telegram?.WebApp
  let initData = tg?.initData || ''
  if (!initData) {
    // Dev fallback: encode user object
    initData = `user=${encodeURIComponent(JSON.stringify(tgUser))}&hash=dev_bypass`
  }

  const data = await signIn(initData)
  setToken(data.access_token)

  // AuthResponse має rank як українську назву (rank_display з бекенду).
  // Нормалізуємо до PlayerProfile-сумісного об'єкта.
  return {
    id:              data.player_id,
    name:            data.name,
    xp:              data.xp,
    rank:            data.rank,          // може бути і 'newbie', і 'Новачок' — Dashboard впорається
    rank_display:    data.rank,          // завжди є після цього нормалізатора
    streak:          0,
    quests_won:      0,
    legendary_wins:  0,
    is_admin:        data.role === 'admin',
    is_new:          data.is_new,
  }
}

// ============================================================
// PLAYERS
// ============================================================
export const getMyProfile = () => req('GET', '/players/me')
export const getHistory   = (limit = 50) => req('GET', `/players/me/history?limit=${limit}`)

// ============================================================
// QUESTS
// ============================================================
export const getActiveQuest = () => req('GET', '/quests/active')

export const submitTextAnswer = (questId, answer) =>
  req('POST', `/quests/${questId}/answer`, { answer })

export const submitPhotoAnswer = (questId, file) => {
  const fd = new FormData()
  fd.append('photo', file)
  const headers = {}
  if (_token) headers['Authorization'] = `Bearer ${_token}`
  return fetch(`${BASE}/quests/${questId}/photo`, {
    method: 'POST', headers, body: fd,
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail))))
}

// ============================================================
// PRIZES
// ============================================================
export const getPrizes           = () => req('GET', '/prizes/')
export const getMyTransactions   = () => req('GET', '/prizes/my-transactions')
export const redeemPrize         = (prizeId) => req('POST', `/prizes/${prizeId}/redeem`)

// ============================================================
// LEADERBOARD
// ============================================================
export const getLeaderboard        = () => req('GET', '/leaderboard/')
export const getLeaderboardWeekly  = () => req('GET', '/leaderboard/weekly')
