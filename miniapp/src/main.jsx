import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'

// Sync Telegram theme to CSS variables
const tg = window.Telegram?.WebApp
if (tg) {
  const p = tg.themeParams
  const r = document.documentElement
  if (p.bg_color)         r.style.setProperty('--tg-bg', p.bg_color)
  if (p.secondary_bg_color) r.style.setProperty('--tg-surface', p.secondary_bg_color)
  if (p.text_color)       r.style.setProperty('--tg-text', p.text_color)
  if (p.hint_color)       r.style.setProperty('--tg-muted', p.hint_color)
  if (p.button_color)     r.style.setProperty('--tg-btn', p.button_color)
  if (p.button_text_color) r.style.setProperty('--tg-btn-text', p.button_text_color)
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
