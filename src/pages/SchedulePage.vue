<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">📅 Расписание занятий</div>
        <div class="page-sub">Сохраняется в базе данных и отображается без наложений</div>
      </div>
      <button class="btn btn-primary" @click="openCreateModal()">
        <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
        Добавить занятие
      </button>
    </div>

    <div class="week-selector">
      <button class="week-nav" @click="prevWeek">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
      </button>
      <div class="week-label">{{ weekLabel }}</div>
      <button class="week-nav" @click="nextWeek">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
      </button>
    </div>

    <div class="schedule-grid">
      <div class="time-column">
        <div class="time-header"></div>
        <div v-for="hour in hours" :key="hour" class="time-slot">
          {{ String(hour).padStart(2, '0') }}:00
        </div>
      </div>

      <div v-for="(day, index) in days" :key="day.name" class="day-column">
        <div class="day-header" :class="{ today: isToday(index) }">
          <div class="day-name">{{ day.name }}</div>
          <div class="day-date">{{ day.date }}</div>
        </div>

        <div class="day-slots">
          <div
            v-for="slot in halfHourSlots"
            :key="`${index}-${slot}`"
            class="hour-slot"
            @click="openCreateModal(index, slot)"
          ></div>

          <div
            v-for="event in layoutedEvents[index]"
            :key="event.id"
            class="schedule-event"
            :style="event.style"
            @click.stop="openEditModal(event)"
          >
            <div class="event-title">{{ event.title }}</div>
            <div class="event-time">{{ event.startTime }} — {{ event.endTime }}</div>
            <div v-if="event.location" class="event-location">📍 {{ event.location }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal" style="max-width: 460px">
        <div class="modal-header">
          <div class="modal-title">{{ editingEvent ? 'Редактировать занятие' : 'Новое занятие' }}</div>
          <button class="modal-close" @click="closeModal">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Название занятия *</label>
            <input class="form-input" v-model="form.title" placeholder="Например: Лекция по математике" />
          </div>

          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label class="form-label">День недели</label>
              <select class="form-input" v-model.number="form.dayIndex">
                <option v-for="(day, i) in dayNames" :key="day" :value="i">{{ day }}</option>
              </select>
            </div>
            <div class="form-group" style="flex:1">
              <label class="form-label">Время начала</label>
              <select class="form-input" v-model.number="form.startMinute">
                <option v-for="minute in startOptions" :key="minute" :value="minute">
                  {{ formatMinute(minute) }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label class="form-label">Продолжительность</label>
              <select class="form-input" v-model.number="form.durationMinutes">
                <option :value="30">30 минут</option>
                <option :value="60">1 час</option>
                <option :value="90">1.5 часа</option>
                <option :value="120">2 часа</option>
                <option :value="180">3 часа</option>
              </select>
            </div>
            <div class="form-group" style="flex:1">
              <label class="form-label">Тип</label>
              <select class="form-input" v-model="form.type">
                <option value="lecture">Лекция</option>
                <option value="practice">Практика</option>
                <option value="lab">Лабораторная</option>
                <option value="seminar">Семинар</option>
                <option value="other">Другое</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Место проведения</label>
            <input class="form-input" v-model="form.location" placeholder="Аудитория 305 / Онлайн" />
          </div>

          <div class="form-group">
            <label class="form-label">Преподаватель</label>
            <input class="form-input" v-model="form.teacher" placeholder="Иванов И.И." />
          </div>

          <div class="form-group">
            <label class="form-label">Цвет</label>
            <div class="color-options">
              <div
                v-for="color in colors"
                :key="color"
                class="color-opt"
                :class="{ selected: form.color === color }"
                :style="{ background: color }"
                @click="form.color = color"
              ></div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button v-if="editingEvent" class="btn btn-ghost btn-danger" @click="removeEvent">Удалить</button>
          <div style="flex:1"></div>
          <button class="btn btn-ghost" @click="closeModal">Отмена</button>
          <button class="btn btn-primary" :disabled="!form.title || saving" @click="saveEvent">
            {{ saving ? 'Сохранение...' : (editingEvent ? 'Сохранить' : 'Добавить') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { addDays, currentDayIndex, formatTimeFromMinutes, getMonday } from '@/utils/dates'

const store = useWorkspaceStore()

const dayNames = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
const hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
const colors = ['#3d52d5', '#e05c2f', '#2d7a4f', '#b45309', '#7c3aed', '#0891b2', '#db2777', '#64748b']
const halfHourSlots = Array.from({ length: hours.length * 2 }, (_, index) => 8 * 60 + index * 30)
const startOptions = [...halfHourSlots]

const SLOT_HEIGHT = 30
const DAY_START_MINUTE = 8 * 60

const currentWeekStart = ref(getMonday(new Date()))
const showModal = ref(false)
const editingEvent = ref(null)
const saving = ref(false)

const form = reactive({
  title: '',
  dayIndex: 0,
  startMinute: 9 * 60,
  durationMinutes: 90,
  location: '',
  teacher: '',
  type: 'lecture',
  color: '#3d52d5',
})

onMounted(() => {
  if (!store.scheduleEvents.length) {
    store.fetchSchedule()
  }
})

const days = computed(() =>
  Array.from({ length: 7 }, (_, index) => {
    const date = addDays(currentWeekStart.value, index)
    return {
      name: dayNames[index],
      date: date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }),
    }
  })
)

const weekLabel = computed(() => {
  const end = addDays(currentWeekStart.value, 6)
  const months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
  return `${currentWeekStart.value.getDate()} ${months[currentWeekStart.value.getMonth()]} — ${end.getDate()} ${months[end.getMonth()]} ${end.getFullYear()}`
})

const layoutedEvents = computed(() => {
  const byDay = Array.from({ length: 7 }, () => [])
  store.scheduleEvents.forEach((event) => {
    byDay[event.dayIndex].push(event)
  })

  return byDay.map((events) => layoutDay(events))
})

function layoutDay(dayEvents) {
  const sorted = [...dayEvents].sort((a, b) => a.startMinute - b.startMinute || a.durationMinutes - b.durationMinutes)
  const groups = []
  let currentGroup = []
  let currentEnd = -1

  sorted.forEach((event) => {
    const eventEnd = event.startMinute + event.durationMinutes
    if (!currentGroup.length || event.startMinute < currentEnd) {
      currentGroup.push(event)
      currentEnd = Math.max(currentEnd, eventEnd)
      return
    }

    groups.push(currentGroup)
    currentGroup = [event]
    currentEnd = eventEnd
  })

  if (currentGroup.length) groups.push(currentGroup)

  return groups.flatMap((group) => {
    const columns = []
    const placed = group.map((event) => {
      let column = columns.findIndex((endMinute) => endMinute <= event.startMinute)
      if (column === -1) {
        column = columns.length
        columns.push(0)
      }
      columns[column] = event.startMinute + event.durationMinutes
      return { ...event, column }
    })

    const columnCount = Math.max(columns.length, 1)

    return placed.map((event) => {
      const widthPercent = 100 / columnCount
      return {
        ...event,
        style: {
          top: `${(event.startMinute - DAY_START_MINUTE) / 30 * SLOT_HEIGHT + 2}px`,
          height: `${Math.max((event.durationMinutes / 30) * SLOT_HEIGHT - 6, 28)}px`,
          left: `calc(${widthPercent * event.column}% + 4px)`,
          width: `calc(${widthPercent}% - 8px)`,
          background: `${event.color}20`,
          borderLeftColor: event.color,
          zIndex: event.column + 2,
        },
      }
    })
  })
}

function isToday(dayIndex) {
  const checkDate = addDays(currentWeekStart.value, dayIndex)
  const now = new Date()
  return now.toDateString() === checkDate.toDateString()
}

function prevWeek() {
  currentWeekStart.value = addDays(currentWeekStart.value, -7)
}

function nextWeek() {
  currentWeekStart.value = addDays(currentWeekStart.value, 7)
}

function openCreateModal(dayIndex = currentDayIndex(), startMinute = 9 * 60) {
  editingEvent.value = null
  Object.assign(form, {
    title: '',
    dayIndex,
    startMinute,
    durationMinutes: 90,
    location: '',
    teacher: '',
    type: 'lecture',
    color: '#3d52d5',
  })
  showModal.value = true
}

function openEditModal(event) {
  editingEvent.value = event
  Object.assign(form, {
    title: event.title,
    dayIndex: event.dayIndex,
    startMinute: event.startMinute,
    durationMinutes: event.durationMinutes,
    location: event.location,
    teacher: event.teacher,
    type: event.type,
    color: event.color,
  })
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingEvent.value = null
}

async function saveEvent() {
  if (!form.title) return

  saving.value = true
  const payload = {
    title: form.title,
    day_index: form.dayIndex,
    start_minute: form.startMinute,
    duration_minutes: form.durationMinutes,
    location: form.location,
    teacher: form.teacher,
    type: form.type,
    color: form.color,
  }

  try {
    if (editingEvent.value) {
      await store.updateScheduleEvent(editingEvent.value.id, payload)
    } else {
      await store.createScheduleEvent(payload)
    }
    closeModal()
  } finally {
    saving.value = false
  }
}

async function removeEvent() {
  if (!editingEvent.value) return
  await store.deleteScheduleEvent(editingEvent.value.id)
  closeModal()
}

function formatMinute(minute) {
  return formatTimeFromMinutes(minute)
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 20px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}
.page-sub {
  color: var(--text-muted);
  font-size: 13.5px;
}
.week-selector {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
}
.week-nav {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.week-nav:hover {
  background: var(--surface-2);
  border-color: var(--accent);
}
.week-nav svg {
  width: 18px;
  height: 18px;
}
.week-label {
  font-size: 15px;
  font-weight: 600;
  min-width: 220px;
  text-align: center;
}
.schedule-grid {
  display: flex;
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.time-column {
  width: 68px;
  flex-shrink: 0;
  background: var(--surface-2);
}
.time-header {
  height: 54px;
  border-bottom: 1px solid var(--border);
}
.time-slot {
  height: 60px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 4px;
  font-size: 11px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-soft);
}
.day-column {
  flex: 1;
  min-width: 120px;
  background: var(--surface);
}
.day-header {
  height: 54px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border);
}
.day-header.today {
  background: var(--accent-light);
}
.day-header.today .day-name {
  color: var(--accent);
}
.day-name {
  font-size: 12px;
  font-weight: 600;
}
.day-date {
  font-size: 11px;
  color: var(--text-muted);
}
.day-slots {
  position: relative;
  height: 780px;
}
.hour-slot {
  height: 30px;
  border-bottom: 1px solid var(--border-soft);
  cursor: pointer;
  transition: background var(--transition);
}
.hour-slot:hover {
  background: var(--surface-2);
}
.schedule-event {
  position: absolute;
  border-radius: 10px;
  border-left: 4px solid;
  padding: 8px 10px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 3px 12px rgba(26, 23, 20, 0.08);
  transition: transform var(--transition), box-shadow var(--transition);
}
.schedule-event:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}
.event-title {
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
  margin-bottom: 2px;
}
.event-time,
.event-location {
  font-size: 10px;
  color: var(--text-muted);
}
.event-location {
  margin-top: 2px;
}
.form-row {
  display: flex;
  gap: 12px;
}
.color-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.color-opt {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color var(--transition), transform var(--transition);
}
.color-opt.selected,
.color-opt:hover {
  border-color: var(--text-primary);
  transform: scale(1.1);
}
.btn-danger {
  color: var(--danger);
}
.btn-danger:hover {
  background: var(--danger-bg);
}

@media (max-width: 1200px) {
  .schedule-grid {
    overflow-x: auto;
  }
  .day-column {
    min-width: 150px;
  }
}
</style>
