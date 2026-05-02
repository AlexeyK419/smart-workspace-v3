<template>
  <div class="card calendar-widget">
    <div class="widget-head">
      <div>
        <div class="card-title">Календарь дедлайнов</div>
        <div class="widget-sub">Компактный обзор месяца и ближайших задач</div>
      </div>
      <div class="cal-nav">
        <button class="cal-nav-btn" @click="prev">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
        </button>
        <div class="cal-month">{{ monthLabel }}</div>
        <button class="cal-nav-btn" @click="next">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
        </button>
      </div>
    </div>

    <div class="calendar-layout">
      <div class="calendar-shell">
        <div class="cal-days-header">
          <div class="cal-day-name" v-for="day in DAY_NAMES" :key="day">{{ day }}</div>
        </div>

        <div class="cal-grid">
          <button
            v-for="cell in cells"
            :key="cell.key"
            class="cal-cell"
            :class="{
              'other-month': !cell.thisMonth,
              today: cell.isToday,
              selected: cell.isSelected,
              'has-assignment': cell.assignments.length,
            }"
            @click="selectCell(cell)"
          >
            <span class="cell-number">{{ cell.day }}</span>
            <div v-if="cell.assignments.length" class="cell-dots">
              <span
                v-for="assignment in cell.assignments.slice(0, 3)"
                :key="assignment.id"
                class="cell-dot"
                :style="{ background: assignment.sourceColor }"
              ></span>
            </div>
            <span v-if="cell.assignments.length > 1" class="cell-count">{{ cell.assignments.length }}</span>
          </button>
        </div>
      </div>

      <div class="calendar-side">
        <div class="side-block">
          <div class="side-title">Выбранная дата</div>
          <div class="selected-label">{{ selectedDateLabel }}</div>

          <div v-if="selectedAssignments.length" class="assignment-stack">
            <button
              v-for="assignment in selectedAssignments"
              :key="assignment.id"
              class="assignment-card"
              @click="selectedAssignment = assignment"
            >
              <div class="assignment-topline">
                <span class="assignment-course-pill" :style="{ background: assignment.sourceColor + '20', color: assignment.sourceColor }">
                  {{ assignment.sourceLabel }}
                </span>
                <span class="assignment-status chip" :class="'chip-' + deadlineChipStatus(assignment)">
                  {{ deadlineStatusLabel(assignment) }}
                </span>
              </div>
              <div class="assignment-name">{{ assignment.title }}</div>
              <div class="assignment-desc">{{ assignment.description || 'Без описания' }}</div>
            </button>
          </div>
          <div v-else class="empty-date">
            На эту дату дедлайнов нет. Ниже показаны ближайшие задания.
          </div>
        </div>

        <div class="side-block">
          <div class="side-title">Ближайшие дедлайны</div>
          <div class="upcoming-list">
            <button
              v-for="assignment in upcomingAssignments"
              :key="assignment.id"
              class="upcoming-item"
              @click="jumpToAssignment(assignment)"
            >
              <span class="upcoming-date">{{ assignment.deadline }}</span>
              <span class="upcoming-name">{{ assignment.title }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedAssignment" class="modal-overlay" @click.self="selectedAssignment = null">
      <div class="modal" style="max-width: 520px">
        <div class="modal-header">
          <div class="modal-title">Информация о задании</div>
          <button class="modal-close" @click="selectedAssignment = null">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <div class="detail-label">Название</div>
            <div class="detail-value detail-title">{{ selectedAssignment.title }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">Источник</div>
            <div class="detail-value">
              <span class="assignment-course-pill" :style="{ background: selectedAssignment.sourceColor + '20', color: selectedAssignment.sourceColor }">
                {{ selectedAssignment.sourceLabel }}
              </span>
            </div>
          </div>
          <div class="detail-row">
            <div class="detail-label">Дедлайн</div>
            <div class="detail-value">{{ selectedAssignment.deadline }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">Описание</div>
            <div class="detail-value">{{ selectedAssignment.description || 'Описание не указано' }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="selectedAssignment = null">Закрыть</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { dateKey, isSameDay, startOfDay } from '@/utils/dates'

const DAY_NAMES = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
const MONTH_NAMES = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

const store = useWorkspaceStore()
const today = startOfDay(new Date())
const year = ref(today.getFullYear())
const month = ref(today.getMonth())
const selectedDate = ref(today)
const selectedAssignment = ref(null)

const assignmentsByDate = computed(() => {
  const map = new Map()
  store.allDeadlines.forEach((assignment) => {
    if (!assignment.deadlineDate) return
    const key = dateKey(assignment.deadlineDate)
    const current = map.get(key) || []
    current.push(assignment)
    map.set(key, current)
  })
  return map
})

const monthLabel = computed(() => `${MONTH_NAMES[month.value]} ${year.value}`)

const selectedAssignments = computed(() => {
  return assignmentsByDate.value.get(dateKey(selectedDate.value)) || []
})

const selectedDateLabel = computed(() =>
  selectedDate.value.toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
)

const upcomingAssignments = computed(() =>
  store.allDeadlines
    .filter((assignment) => assignment.deadlineDate && assignment.deadlineDate >= today)
    .slice(0, 5)
)

const cells = computed(() => {
  const list = []
  const first = new Date(year.value, month.value, 1)
  let startDay = first.getDay()
  startDay = startDay === 0 ? 6 : startDay - 1

  const daysInMonth = new Date(year.value, month.value + 1, 0).getDate()
  const prevDays = new Date(year.value, month.value, 0).getDate()

  for (let i = 0; i < startDay; i++) {
    const date = new Date(year.value, month.value - 1, prevDays - startDay + i + 1)
    list.push(makeCell(`p${i}`, date, false))
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year.value, month.value, day)
    list.push(makeCell(`c${day}`, date, true))
  }

  let nextDay = 1
  while (list.length < 42) {
    const date = new Date(year.value, month.value + 1, nextDay)
    list.push(makeCell(`n${nextDay}`, date, false))
    nextDay += 1
  }

  return list
})

function makeCell(key, date, thisMonth) {
  return {
    key,
    date,
    day: date.getDate(),
    thisMonth,
    assignments: assignmentsByDate.value.get(dateKey(date)) || [],
    isToday: isSameDay(date, today),
    isSelected: isSameDay(date, selectedDate.value),
  }
}

function selectCell(cell) {
  if (!cell.thisMonth) {
    month.value = cell.date.getMonth()
    year.value = cell.date.getFullYear()
  }
  selectedDate.value = startOfDay(cell.date)
}

function jumpToAssignment(assignment) {
  if (!assignment.deadlineDate) return
  selectedDate.value = startOfDay(assignment.deadlineDate)
  month.value = assignment.deadlineDate.getMonth()
  year.value = assignment.deadlineDate.getFullYear()
  selectedAssignment.value = assignment
}

function deadlineChipStatus(item) {
  if (item.kind !== 'project') return item.status
  return { todo: 'pending', in_progress: 'progress', done: 'done' }[item.status] ?? 'pending'
}

function deadlineStatusLabel(item) {
  if (item.kind === 'project') return store.projectTaskStatusLabel(item.status)
  return store.statusLabel(item.status)
}

function prev() {
  if (month.value === 0) {
    month.value = 11
    year.value -= 1
  } else {
    month.value -= 1
  }
}

function next() {
  if (month.value === 11) {
    month.value = 0
    year.value += 1
  } else {
    month.value += 1
  }
}
</script>

<style scoped>
.calendar-widget {
  margin-bottom: 18px;
  padding: 18px;
}
.widget-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}
.widget-sub {
  font-size: 12.5px;
  color: var(--text-muted);
  margin-top: 4px;
}
.cal-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}
.cal-month {
  min-width: 130px;
  text-align: center;
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
}
.cal-nav-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cal-nav-btn:hover {
  background: var(--surface-2);
}
.cal-nav-btn svg {
  width: 16px;
  height: 16px;
}
.calendar-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 270px;
  gap: 18px;
}
.calendar-shell {
  padding: 14px;
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--surface) 96%, transparent),
    color-mix(in srgb, var(--surface-2) 88%, transparent)
  );
}
.cal-days-header,
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}
.cal-days-header {
  margin-bottom: 8px;
}
.cal-day-name {
  text-align: center;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
}
.cal-cell {
  position: relative;
  min-height: 40px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  padding: 6px 4px 4px;
  transition: transform var(--transition), border-color var(--transition), background var(--transition);
}
.cal-cell:hover {
  border-color: var(--border);
  background: var(--surface-2);
}
.cal-cell.other-month {
  opacity: 0.35;
}
.cal-cell.today {
  border-color: var(--accent-mid);
  background: var(--accent-light);
}
.cal-cell.selected {
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
}
.cell-number {
  display: block;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
}
.cell-dots {
  display: flex;
  justify-content: center;
  gap: 4px;
  margin-top: 5px;
}
.cell-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.cell-count {
  position: absolute;
  top: 4px;
  right: 6px;
  font-size: 9px;
  color: var(--text-muted);
}
.calendar-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.side-block {
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  padding: 14px;
  background: var(--surface);
}
.side-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.selected-label {
  font-family: var(--font-display);
  font-size: 18px;
  margin-bottom: 12px;
  text-transform: capitalize;
}
.assignment-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.assignment-card,
.upcoming-item {
  width: 100%;
  text-align: left;
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  background: var(--surface);
  padding: 11px 12px;
  cursor: pointer;
}
.assignment-card:hover,
.upcoming-item:hover {
  background: var(--surface-2);
}
.assignment-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.assignment-course-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 600;
}
.assignment-name {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}
.assignment-desc,
.empty-date,
.upcoming-date,
.upcoming-name,
.detail-label,
.detail-value {
  color: var(--text-secondary);
}
.assignment-desc,
.empty-date {
  font-size: 12px;
  line-height: 1.5;
}
.upcoming-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.upcoming-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.upcoming-date {
  font-size: 11px;
}
.upcoming-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.detail-row {
  margin-bottom: 16px;
}
.detail-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

@media (max-width: 1080px) {
  .calendar-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .calendar-widget {
    padding: 16px;
  }

  .widget-head {
    align-items: center;
    margin-bottom: 14px;
  }

  .widget-sub {
    display: none;
  }

  .cal-month {
    min-width: 86px;
    font-size: 14px;
  }

  .calendar-shell,
  .side-block {
    border-radius: 18px;
  }

  .calendar-shell {
    padding: 12px;
  }

  .cal-days-header,
  .cal-grid {
    gap: 5px;
  }

  .cal-cell {
    min-height: 44px;
    border-radius: 12px;
  }

  .calendar-side {
    gap: 10px;
  }
}
</style>
