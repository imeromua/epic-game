import React, { useState, useEffect, useRef } from 'react'
import { useApp } from '../App'
import Spinner from '../components/Spinner'
import Countdown from '../components/Countdown'
import { getActiveQuest, submitTextAnswer, submitPhotoAnswer } from '../api'
import { useTelegram } from '../hooks/useTelegram'

export default function QuestPage() {
  const { showToast } = useApp()
  const { haptic } = useTelegram()
  const [quest, setQuest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [answer, setAnswer] = useState('')
  const [choice, setChoice] = useState(null)
  const [photo, setPhoto] = useState(null)
  const [preview, setPreview] = useState(null)
  const fileRef = useRef()

  useEffect(() => { loadQuest() }, [])

  const loadQuest = () => {
    setLoading(true)
    getActiveQuest()
      .then(setQuest)
      .catch(() => setQuest(null))
      .finally(() => setLoading(false))
  }

  const handlePhoto = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhoto(file)
    setPreview(URL.createObjectURL(file))
    haptic('medium')
  }

  const canSubmit = () => {
    if (!quest || done || submitting) return false
    if (quest.quest_type === 'text')   return answer.trim().length >= 2
    if (quest.quest_type === 'choice') return choice !== null
    if (quest.quest_type === 'photo')  return photo !== null
    return false
  }

  const handleSubmit = async () => {
    if (!canSubmit()) return
    haptic('medium')
    setSubmitting(true)
    try {
      if (quest.quest_type === 'photo') {
        await submitPhotoAnswer(quest.id, photo)
        showToast('📸 Фото надіслано! Очікуй підтвердження від адміна.')
      } else {
        const ans = quest.quest_type === 'choice' ? (choice ? 'Так' : 'Ні') : answer
        const res = await submitTextAnswer(quest.id, ans)
        if (res.is_winner) {
          showToast(`🏆 Ти переміг! +${res.xp_earned} XP`)
          window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
        } else {
          showToast('Відповідь прийнята! Але хтось виявився швидшим 😔')
        }
      }
      setDone(true)
    } catch (e) {
      showToast(`❌ ${e.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return (
    <div className="page" style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
      <Spinner />
    </div>
  )

  if (!quest) return (
    <div className="page">
      <div className="quest-empty">
        <div className="quest-empty-icon">🎯</div>
        <h2>Квестів поки немає</h2>
        <p>Бот автоматично запустить наступне завдання. Слідкуй за повідомленнями!</p>
      </div>
    </div>
  )

  if (done) return (
    <div className="page">
      <div className="quest-empty">
        <div style={{ fontSize: 64 }}>✅</div>
        <h2>Відповідь надіслана!</h2>
        <p>Результат буде повідомлений у чат команди.</p>
        <button className="btn btn-primary" style={{ marginTop: 24, width: 'auto', padding: '12px 32px' }} onClick={loadQuest}>
          Оновити
        </button>
      </div>
    </div>
  )

  const options = quest.answer_options ? JSON.parse(quest.answer_options) : ['Так', 'Ні']
  const endsAt = quest.started_at
    ? new Date(new Date(quest.started_at).getTime() + quest.time_limit_minutes * 60000).toISOString()
    : null

  const typeBadge = { photo: 'badge-photo', text: 'badge-text', choice: 'badge-choice' }
  const typeEmoji = { photo: '📸 Фото', text: '✏️ Текст', choice: '🔘 Вибір' }

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title">⚡ Квест</div>
        <span className={`quest-type-badge ${typeBadge[quest.quest_type]}`}>
          {typeEmoji[quest.quest_type]}
        </span>
      </div>

      {/* Countdown */}
      {endsAt && <Countdown endsAt={endsAt} onExpire={loadQuest} />}

      {/* Quest description */}
      <div className="card">
        <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>{quest.title}</div>
        <div style={{ fontSize: 14, color: 'var(--muted)', lineHeight: 1.5 }}>{quest.description}</div>
        <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span className="pill" style={{ background: 'var(--teal-dim)', color: 'var(--teal)' }}>
            +{quest.xp_reward} XP
          </span>
          {quest.prize_name && (
            <span className="pill" style={{ background: 'var(--gold-dim)', color: 'var(--gold)' }}>
              {quest.prize_emoji} {quest.prize_name}
            </span>
          )}
        </div>
      </div>

      {/* Answer area */}
      <div className="card" style={{ marginTop: 12 }}>
        {quest.quest_type === 'text' && (
          <textarea
            className="answer-input"
            rows={3}
            placeholder="Введи свою відповідь..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
        )}

        {quest.quest_type === 'choice' && (
          <div className="choice-buttons">
            {options.map((opt, i) => (
              <button
                key={i}
                className={`choice-btn${choice === i ? ' selected' : ''}`}
                onClick={() => { setChoice(i); haptic('light') }}
              >
                {opt}
              </button>
            ))}
          </div>
        )}

        {quest.quest_type === 'photo' && (
          <div className={`photo-upload-zone${photo ? ' has-photo' : ''}`}>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handlePhoto}
            />
            {!photo ? (
              <>
                <div style={{ fontSize: 40, marginBottom: 8 }}>📷</div>
                <div style={{ fontWeight: 600 }}>Натисни, щоб зробити фото</div>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Камера відкриється автоматично</div>
              </>
            ) : (
              <>
                <div style={{ color: 'var(--green)', fontWeight: 600, marginBottom: 8 }}>✅ Фото готове</div>
                <img src={preview} alt="preview" className="photo-preview" />
              </>
            )}
          </div>
        )}

        <button
          className="btn btn-primary"
          disabled={!canSubmit()}
          onClick={handleSubmit}
        >
          {submitting ? '⏳ Надсилаємо...' : '🚀 Надіслати відповідь'}
        </button>
      </div>
    </div>
  )
}
