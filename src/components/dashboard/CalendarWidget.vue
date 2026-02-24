<template>
  <div class="card calendar-widget">
    <div class="cal-header">
      <div class="cal-month">{{ monthLabel }}</div>
      <div class="cal-nav">
        <button class="cal-nav-btn" @click="prev">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
        </button>
        <button class="cal-nav-btn" @click="next">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
        </button>
      </div>
    </div>
    <div class="cal-days-header">
      <div class="cal-day-name" v-for="d in DAY_NAMES" :key="d">{{ d }}</div>
    </div>
    <div class="cal-grid">
      <div
        v-for="cell in cells" :key="cell.key"
        class="cal-cell"
        :class="{ 'other-month': !cell.thisMonth, 'today': cell.isToday, 'has-event': cell.hasEvent }"
      >{{ cell.day }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const DAY_NAMES   = ['пн','вт','ср','чт','пт','сб','вс']
const MONTH_NAMES = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
const EVENT_DAYS  = new Set([5, 10, 15, 19, 22, 28])

const now   = new Date()
const year  = ref(now.getFullYear())
const month = ref(now.getMonth())

const monthLabel = computed(() => `${MONTH_NAMES[month.value]} ${year.value}`)

const cells = computed(() => {
  const list = []
  const first = new Date(year.value, month.value, 1)
  let startDay = first.getDay()
  startDay = startDay === 0 ? 6 : startDay - 1
  const daysInMonth = new Date(year.value, month.value + 1, 0).getDate()
  const prevDays    = new Date(year.value, month.value, 0).getDate()
  for (let i = 0; i < startDay; i++)
    list.push({ key: `p${i}`, day: prevDays - startDay + i + 1, thisMonth: false, isToday: false, hasEvent: false })
  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = d === now.getDate() && month.value === now.getMonth() && year.value === now.getFullYear()
    list.push({ key: `c${d}`, day: d, thisMonth: true, isToday, hasEvent: EVENT_DAYS.has(d) })
  }
  let nd = 1
  while (list.length % 7 !== 0)
    list.push({ key: `n${nd}`, day: nd++, thisMonth: false, isToday: false, hasEvent: false })
  return list
})

function prev() { if (month.value === 0) { month.value = 11; year.value-- } else month.value-- }
function next() { if (month.value === 11) { month.value = 0; year.value++ } else month.value++ }
</script>

<style scoped>
.calendar-widget { margin-bottom: 12px; padding: 10px 12px; }

.cal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.cal-month  { font-family: var(--font-display); font-size: 12px; font-weight: 600; }
.cal-nav    { display: flex; gap: 2px; }
.cal-nav-btn {
  width: 20px; height: 20px; border-radius: 4px;
  border: 1px solid var(--border); background: transparent;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background var(--transition);
}
.cal-nav-btn:hover { background: var(--surface-2); }
.cal-nav-btn svg { width: 10px; height: 10px; }

.cal-days-header { display: grid; grid-template-columns: repeat(7,1fr); gap: 1px; margin-bottom: 1px; }
.cal-day-name {
  text-align: center; font-size: 8px; font-weight: 600;
  color: var(--text-muted); padding: 1px;
  letter-spacing: 0.3px; text-transform: uppercase;
}

.cal-grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 1px; }
.cal-cell {
  aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
  border-radius: 3px; font-size: 9px; cursor: pointer;
  transition: background var(--transition); position: relative;
}
.cal-cell:hover           { background: var(--surface-2); }
.cal-cell.other-month     { color: var(--text-muted); opacity: 0.35; }
.cal-cell.today           { background: var(--accent); color: white; font-weight: 700; }
.cal-cell.has-event::after {
  content: ''; position: absolute; bottom: 1px; left: 50%;
  transform: translateX(-50%); width: 2px; height: 2px;
  border-radius: 50%; background: var(--accent);
}
.cal-cell.today::after { background: rgba(255,255,255,0.65); }
</style>