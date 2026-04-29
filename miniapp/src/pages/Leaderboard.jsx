import React, { useState, useEffect } from 'react'
import Spinner from '../components/Spinner'
import { getLeaderboard, getLeaderboardWeekly } from '../api'
import { useApp } from '../App'

const RANK_COLORS = {
  'Новачок':          '#6b7280',
  'Слідопит':         '#3b82f6',
  'Знавець Залу':     '#06b6d4',
  'Майстер Свіжості': '#f59e0b',
  'Легенда':          '#a855f7',
}

export default function Leaderboard() {
  const { player } = useApp()
  const [tab, setTab] = useState('month')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const fn = tab === 'month' ? getLeaderboard : getLeaderboardWeekly
    fn()
      .then((r) => setData(r.leaderboard || r || []))
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [tab])

  const top3 = data.slice(0, 3)
  const rest = data.slice(3)

  const avatarLetter = (name) => (name || '?')[0].toUpperCase()
  const isMe = (row) => row.player_id === player?.player_id

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title">🏆 Рейтинг</div>
      </div>

      <div className="lb-tabs">
        <button className={`lb-tab${tab === 'month' ? ' active' : ''}`} onClick={() => setTab('month')}>
          За місяць
        </button>
        <button className={`lb-tab${tab === 'week' ? ' active' : ''}`} onClick={() => setTab('week')}>
          За тиждень
        </button>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}><Spinner /></div>
      ) : (
        <>
          {/* Podium */}
          {top3.length >= 3 && (
            <div className="podium">
              {/* 2nd */}
              <div className="podium-item p2">
                <div className="podium-avatar">{avatarLetter(top3[1]?.name)}</div>
                <div className="podium-name">{(top3[1]?.name || '').split(' ')[0]}</div>
                <div className="podium-xp">{top3[1]?.xp} XP</div>
                <div className="podium-stand">2</div>
              </div>
              {/* 1st */}
              <div className="podium-item p1">
                <div className="podium-avatar">
                  <span className="podium-crown">👑</span>
                  {avatarLetter(top3[0]?.name)}
                </div>
                <div className="podium-name">{(top3[0]?.name || '').split(' ')[0]}</div>
                <div className="podium-xp">{top3[0]?.xp} XP</div>
                <div className="podium-stand">1</div>
              </div>
              {/* 3rd */}
              <div className="podium-item p3">
                <div className="podium-avatar">{avatarLetter(top3[2]?.name)}</div>
                <div className="podium-name">{(top3[2]?.name || '').split(' ')[0]}</div>
                <div className="podium-xp">{top3[2]?.xp} XP</div>
                <div className="podium-stand">3</div>
              </div>
            </div>
          )}

          {/* Rest of leaderboard */}
          <div className="card">
            {rest.length === 0 && data.length === 0 && (
              <div className="empty-list">Поки що немає даних 🙁</div>
            )}
            {rest.map((row, i) => (
              <div key={row.player_id} className={`lb-row${isMe(row) ? ' is-me' : ''}`}>
                <div className="lb-pos">{i + 4}</div>
                <div className="lb-avatar"
                  style={{ background: RANK_COLORS[row.rank] ? `${RANK_COLORS[row.rank]}22` : undefined,
                           color: RANK_COLORS[row.rank] }}>
                  {avatarLetter(row.name)}
                </div>
                <div className="lb-info">
                  <div className="lb-info-name">{row.name}{isMe(row) ? ' 👈' : ''}</div>
                  <div className="lb-info-rank">{row.rank}</div>
                </div>
                <div className="lb-xp">{row.xp}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
