import React, { useEffect, useState } from 'react'
import Spinner from '../components/Spinner'
import { getHistory } from '../api'

export default function HistoryPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getHistory(50)
      .then((r) => setItems(r.history || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [])

  const fmtDate = (d) =>
    d
      ? new Date(d).toLocaleDateString('uk', {
          day: 'numeric',
          month: 'short',
          hour: '2-digit',
          minute: '2-digit',
        })
      : ''

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title">📖 Історія</div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
          <Spinner />
        </div>
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
          {items.map((item, i) => {
            const isWin  = item.type === 'quest' && item.is_winner
            const isPrize = item.type === 'prize'
            return (
              <div key={i} className="history-item">
                <div className={`history-icon ${isWin ? 'win' : isPrize ? 'prize' : 'lose'}`}>
                  {item.emoji}
                </div>
                <div className="history-body">
                  <div className="history-title">{item.title}</div>
                  <div className="history-sub">
                    {item.subtitle} · {fmtDate(item.date)}
                  </div>
                </div>
                {item.xp_earned > 0 && (
                  <div className="history-xp">+{item.xp_earned} XP</div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
