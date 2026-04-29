import React, { useEffect, useState } from 'react'
import { useApp } from '../App'
import Spinner from '../components/Spinner'
import { getActiveQuest, getMyProfile } from '../api'

// rank може прийти як lowercase ('newbie') або українською назвою ('Новачок')
// цей мап покриває обидва варіанти
const TO_KEY = {
  'newbie':           'newbie',
  'scout':            'scout',
  'expert':           'expert',
  'master':           'master',
  'legend':           'legend',
  'Новачок':         'newbie',
  'Слідопит':         'scout',
  'Знавець Залу':     'expert',
  'Майстер Свіжості': 'master',
  'Легенда':           'legend',
}

const RANK_DISPLAY = {
  newbie:  'Новачок',
  scout:   'Слідопит',
  expert:  'Знавець Залу',
  master:  'Майстер Свіжості',
  legend:  'Легенда',
}

const XP_NEXT = { newbie: 100, scout: 300, expert: 600, master: 1000, legend: 9999 }
const XP_FROM = { newbie: 0,   scout: 100, expert: 300, master: 600,  legend: 1000 }
const RANK_EMOJIS = { newbie: '🌱', scout: '🔍', expert: '🎯', master: '⭐', legend: '👑' }

export default function Dashboard() {
  const { player, setTab } = useApp()
  const [profile, setProfile] = useState(null)
  const [quest, setQuest] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([getMyProfile(), getActiveQuest()])
      .then(([p, q]) => {
        if (p.status === 'fulfilled') setProfile(p.value)
        if (q.status === 'fulfilled') setQuest(q.value)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="page" style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
      <Spinner />
    </div>
  )

  const data    = profile || player
  const rankKey = TO_KEY[data?.rank] || 'newbie'

  // rank_display: profile повертає rank_display; auth-об'`єкт має rank як дисплей назву
  const rankDisplay = data?.rank_display || RANK_DISPLAY[rankKey] || 'Новачок'

  const xp     = data?.xp || 0
  const xpFrom = XP_FROM[rankKey] || 0
  const xpTo   = XP_NEXT[rankKey] || 1000
  const xpPct  = Math.min(100, Math.round(((xp - xpFrom) / (xpTo - xpFrom)) * 100))

  return (
    <div className="page">
      {/* Rank Hero Card */}
      <div className={`rank-card rank-${rankKey}-card`}>
        <div className="rank-badge-icon">{RANK_EMOJIS[rankKey]}</div>
        <div className="rank-card-label">Твій ранг</div>
        <div className="rank-card-name">{rankDisplay}</div>
        <div className="rank-card-player">{data?.name}</div>
        <div className="rank-card-xp">
          <div className="xp-bar-bg">
            <div className="xp-bar-fill" style={{ width: `${xpPct}%` }} />
          </div>
          <div className="xp-bar-label">
            <span>{xp} XP</span>
            <span>до наступного: {xpTo}</span>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--teal)' }}>{data?.quests_won ?? 0}</div>
          <div className="stat-label">Перемог</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--orange)' }}>
            🔥{profile?.streak ?? 0}
          </div>
          <div className="stat-label">Серія днів</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--purple)' }}>
            💎{data?.legendary_wins ?? 0}
          </div>
          <div className="stat-label">Легенд.</div>
        </div>
      </div>

      {/* Active Quest Banner */}
      {quest && (
        <>
          <p className="section-title">Активний квест</p>
          <div className="quest-banner" onClick={() => setTab('quest')}>
            <div className="quest-banner-icon">⚡</div>
            <div>
              <h3>{quest.title}</h3>
              <p>{quest.description}</p>
              <div className="quest-banner-timer">+{quest.xp_reward} XP · Тиснути для відповіді →</div>
            </div>
          </div>
        </>
      )}

      {!quest && (
        <div className="card" style={{ marginTop: 16, textAlign: 'center', color: 'var(--muted)', fontSize: 14, padding: '24px 16px' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>😴</div>
          Квестів зараз немає. Бот повідомить, коли почнеться нове завдання.
        </div>
      )}

      {/* XP info */}
      <p className="section-title">Про рейтинг</p>
      <div className="card" style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6 }}>
        Виконуй квести першим — отримуй XP і піднімайся в рейтингу команди.
        Щомісяця переможець отримує
        <span style={{ color: 'var(--gold)', fontWeight: 700 }}> 💎 Легендарну нагороду</span>.
      </div>
    </div>
  )
}
