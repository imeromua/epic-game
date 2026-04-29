import React, { useState, useEffect } from 'react'
import { useApp } from '../App'
import Spinner from '../components/Spinner'
import { getPrizes, getMyTransactions, redeemPrize } from '../api'
import { useTelegram } from '../hooks/useTelegram'

const CAT_LABELS = { 1: '⭐ Easy', 2: '⭐⭐ Medium', 3: '⭐⭐⭐ Hard', 4: '💎 Legendary' }
const STARS = { 1: '⭐', 2: '⭐⭐', 3: '⭐⭐⭐', 4: '💎' }

export default function PrizeShop() {
  const { showToast } = useApp()
  const { haptic, showConfirm } = useTelegram()
  const [tab, setTab] = useState('shop')
  const [prizes, setPrizes] = useState([])
  const [txs, setTxs] = useState([])
  const [filter, setFilter] = useState(0)
  const [loading, setLoading] = useState(true)
  const [redeeming, setRedeeming] = useState(null)

  useEffect(() => {
    setLoading(true)
    const fn = tab === 'shop' ? getPrizes : getMyTransactions
    fn()
      .then((r) => {
        if (tab === 'shop') setPrizes(r.prizes || r || [])
        else setTxs(r.transactions || r || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [tab])

  const handleRedeem = async (prize) => {
    const ok = await showConfirm(`Обміняти ${prize.xp_cost} XP на ${prize.emoji} ${prize.name}?`)
    if (!ok) return
    haptic('medium')
    setRedeeming(prize.id)
    try {
      await redeemPrize(prize.id)
      showToast(`🎉 ${prize.emoji} ${prize.name} отримано!`)
      haptic('heavy')
    } catch (e) {
      showToast(`❌ ${e.message}`)
    } finally {
      setRedeeming(null)
    }
  }

  const filtered = filter === 0 ? prizes : prizes.filter((p) => p.category === filter)
  const cats = [0, ...new Set(prizes.map((p) => p.category))].sort()

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('uk', { day: 'numeric', month: 'short' }) : ''

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title">🎁 Призи</div>
      </div>

      {/* Main / My prizes tabs */}
      <div className="lb-tabs" style={{ marginBottom: 12 }}>
        <button className={`lb-tab${tab === 'shop' ? ' active' : ''}`} onClick={() => setTab('shop')}>Магазин</button>
        <button className={`lb-tab${tab === 'my' ? ' active' : ''}`} onClick={() => setTab('my')}>Мої призи</button>
      </div>

      {tab === 'shop' && (
        <>
          {/* Category filters */}
          <div className="shop-tabs">
            {cats.map((c) => (
              <button
                key={c}
                className={`shop-tab${filter === c ? ' active' : ''}`}
                onClick={() => setFilter(c)}
              >
                {c === 0 ? '🎯 Всі' : CAT_LABELS[c]}
              </button>
            ))}
          </div>

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}><Spinner /></div>
          ) : (
            <div className="prize-grid">
              {filtered.map((prize) => (
                <div key={prize.id} className={`prize-card${prize.is_rare ? ' rare' : ''}`}>
                  <div className="prize-emoji">{prize.emoji}</div>
                  <div className="prize-name">{prize.name}</div>
                  <div className="prize-stars">{STARS[prize.category]}</div>
                  {prize.xp_cost > 0 && (
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>{prize.xp_cost} XP</div>
                  )}
                  <button
                    className="prize-btn"
                    onClick={() => handleRedeem(prize)}
                    disabled={redeeming === prize.id}
                  >
                    {redeeming === prize.id ? '⏳' : 'Отримати'}
                  </button>
                </div>
              ))}
              {filtered.length === 0 && <div className="empty-list" style={{ gridColumn: '1/-1' }}>Призів не знайдено</div>}
            </div>
          )}
        </>
      )}

      {tab === 'my' && (
        <div className="card">
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 24 }}><Spinner /></div>
          ) : txs.length === 0 ? (
            <div className="empty-list">Поки що жодного призу 🙁<br />Виконуй квести та перемагай!</div>
          ) : txs.map((tx) => (
            <div key={tx.id} className="tx-row">
              <div className="tx-emoji">{tx.prize_emoji || '🎁'}</div>
              <div className="tx-info">
                <div className="tx-name">{tx.prize_name}</div>
                <div className="tx-date">{fmtDate(tx.created_at)}</div>
              </div>
              <div className={`tx-status ${tx.is_issued ? 'issued' : 'pending'}`}>
                {tx.is_issued ? '✅ Видано' : '⏳ Очікує'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
