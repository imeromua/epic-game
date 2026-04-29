export function useTelegram() {
  const tg = window.Telegram?.WebApp

  const haptic = (type = 'light') => {
    tg?.HapticFeedback?.impactOccurred(type)
  }

  const vibrate = () => {
    tg?.HapticFeedback?.notificationOccurred('success')
  }

  const showConfirm = (message) =>
    new Promise((resolve) => {
      if (tg?.showConfirm) {
        tg.showConfirm(message, (ok) => resolve(ok))
      } else {
        resolve(window.confirm(message))
      }
    })

  const close = () => tg?.close()

  return { tg, haptic, vibrate, showConfirm, close }
}
