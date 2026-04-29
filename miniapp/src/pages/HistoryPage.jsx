import React, { useEffect, useState } from 'react'
import Spinner from '../components/Spinner'
import { getMyProfile } from '../api'

// History uses the quest_results from the profile endpoint
// In real app you'd add GET /players/me/history endpoint
export default function HistoryPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Stub: in full impl this calls GET /players/me/history
    // For MVP we show the placeholder with structure ready
    setLoading(false)
    setItems([])
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title">📖 Історія</div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}><Spinner /></div>
      ) : items.length === 0 ? (
        <div className="card">
          <div className="empty-list">
            <div style={{ fontSize: 40, marginBottom: 8 }}>📭</div>
            Твоя історія ще порожня.<br />
            Виграй перший квест — він з'явиться тут!
          </div>
        </div>
      ) : (
        <div className="card">
          {items.map((item, i) => (
            <div key={i} className="history-item">
              <div className={`history-icon ${item.is_winner ? 'win' : 'lose'}`}>
                {item.is_winner ? '🏆' : '👀'}
              </div>
              <div className="history-body">
                <div className="history-title">{item.quest_title}</div>
                <div className="history-sub">{item.date}</div>
              </div>
              {item.is_winner && (
                <div className="history-xp">+{item.xp_earned} XP</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
