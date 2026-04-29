import React, { useState, useEffect } from 'react'

export default function Countdown({ endsAt, onExpire }) {
  const calc = () => Math.max(0, Math.floor((new Date(endsAt) - Date.now()) / 1000))
  const [sec, setSec] = useState(calc)

  useEffect(() => {
    const id = setInterval(() => {
      const s = calc()
      setSec(s)
      if (s === 0) { clearInterval(id); onExpire?.() }
    }, 1000)
    return () => clearInterval(id)
  }, [endsAt])

  const m = String(Math.floor(sec / 60)).padStart(2, '0')
  const s = String(sec % 60).padStart(2, '0')

  return (
    <div className="countdown">
      <div className={`countdown-digits${sec < 30 ? ' urgent' : ''}`}>{m}:{s}</div>
      <div className="countdown-label">залишилось</div>
    </div>
  )
}
