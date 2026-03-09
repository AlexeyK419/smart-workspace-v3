const RU_MONTHS = {
  янв: 0, января: 0,
  фев: 1, февраля: 1,
  мар: 2, марта: 2,
  апр: 3, апреля: 3,
  май: 4, мая: 4,
  июн: 5, июня: 5,
  июл: 6, июля: 6,
  авг: 7, августа: 7,
  сен: 8, сент: 8, сентября: 8,
  окт: 9, октября: 9,
  ноя: 10, ноября: 10,
  дек: 11, декабря: 11,
}

export function parseRuDate(value) {
  if (!value) return null
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value

  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase().replace(',', ' ')
    const isoCandidate = new Date(normalized)
    if (!Number.isNaN(isoCandidate.getTime()) && /^\d{4}-\d{2}-\d{2}/.test(normalized)) {
      return isoCandidate
    }

    const match = normalized.match(/^(\d{1,2})\s+([а-яё]+)\s+(\d{4})$/i)
    if (match) {
      const [, dayRaw, monthRaw, yearRaw] = match
      const monthIndex = RU_MONTHS[monthRaw]
      if (monthIndex !== undefined) {
        return new Date(Number(yearRaw), monthIndex, Number(dayRaw))
      }
    }
  }

  return null
}

export function startOfDay(value) {
  const date = value instanceof Date ? new Date(value) : new Date(value)
  date.setHours(0, 0, 0, 0)
  return date
}

export function isSameDay(a, b) {
  if (!a || !b) return false
  return startOfDay(a).getTime() === startOfDay(b).getTime()
}

export function formatTimeFromMinutes(totalMinutes) {
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

export function getMonday(date) {
  const value = new Date(date)
  const day = value.getDay()
  const diff = value.getDate() - day + (day === 0 ? -6 : 1)
  value.setDate(diff)
  value.setHours(0, 0, 0, 0)
  return value
}

export function addDays(date, amount) {
  const next = new Date(date)
  next.setDate(next.getDate() + amount)
  return next
}

export function currentDayIndex(date = new Date()) {
  return (date.getDay() + 6) % 7
}

export function dateKey(date) {
  const normalized = startOfDay(date)
  const year = normalized.getFullYear()
  const month = String(normalized.getMonth() + 1).padStart(2, '0')
  const day = String(normalized.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
