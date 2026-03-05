<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">📅 Расписание занятий</div>
        <div class="page-sub">Составьте своё расписание на неделю</div>
      </div>
      <button class="btn btn-primary" @click="showAddModal = true">
        <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
        Добавить занятие
      </button>
    </div>

    <!-- Week selector -->
    <div class="week-selector">
      <button class="week-nav" @click="prevWeek">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
      </button>
      <div class="week-label">{{ weekLabel }}</div>
      <button class="week-nav" @click="nextWeek">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
      </button>
    </div>

    <!-- Schedule grid -->
    <div class="schedule-grid">
      <!-- Time column -->
      <div class="time-column">
        <div class="time-header"></div>
        <div v-for="hour in hours" :key="hour" class="time-slot">
          {{ hour }}:00
        </div>
      </div>

      <!-- Day columns -->
      <div v-for="(day, index) in days" :key="day.name" class="day-column">
        <div class="day-header" :class="{ today: isToday(index) }">
          <div class="day-name">{{ day.name }}</div>
          <div class="day-date">{{ day.date }}</div>
        </div>
        <div class="day-slots">
          <div v-for="hour in hours" :key="hour" class="hour-slot" @click="addAtTime(index, hour)">
            <!-- Events for this hour -->
            <div
              v-for="event in getEventsAt(index, hour)"
              :key="event.id"
              class="schedule-event"
              :style="{ 
                background: event.color + '20', 
                borderLeftColor: event.color,
                height: (event.duration * 60 - 4) + 'px'
              }"
              @click.stop="editEvent(event)"
            >
              <div class="event-title">{{ event.title }}</div>
              <div class="event-time">{{ event.startTime }} - {{ event.endTime }}</div>
              <div class="event-location" v-if="event.location">📍 {{ event.location }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal" style="max-width: 440px">
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
              <select class="form-input" v-model="form.dayIndex">
                <option v-for="(day, i) in dayNames" :key="i" :value="i">{{ day }}</option>
              </select>
            </div>
            <div class="form-group" style="flex:1">
              <label class="form-label">Время начала</label>
              <select class="form-input" v-model="form.startHour">
                <option v-for="h in hours" :key="h" :value="h">{{ h }}:00</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label class="form-label">Продолжительность</label>
              <select class="form-input" v-model="form.duration">
                <option :value="0.5">30 минут</option>
                <option :value="1">1 час</option>
                <option :value="1.5">1.5 часа</option>
                <option :value="2">2 часа</option>
                <option :value="3">3 часа</option>
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
              <div v-for="c in colors" :key="c" class="color-opt"
                :class="{ selected: form.color === c }"
                :style="{ background: c }"
                @click="form.color = c"></div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button v-if="editingEvent" class="btn btn-ghost btn-danger" @click="deleteEvent">Удалить</button>
          <div style="flex:1"></div>
          <button class="btn btn-ghost" @click="closeModal">Отмена</button>
          <button class="btn btn-primary" :disabled="!form.title" @click="saveEvent">
            {{ editingEvent ? 'Сохранить' : 'Добавить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const dayNames = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
const hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
const colors = ['#3d52d5', '#e05c2f', '#2d7a4f', '#b45309', '#7c3aed', '#0891b2', '#db2777', '#64748b']

const currentWeekStart = ref(getMonday(new Date()))
const showAddModal = ref(false)
const editingEvent = ref(null)

const events = ref([
  {
    id: 1,
    title: 'Алгоритмы и структуры данных',
    dayIndex: 0,
    startHour: 9,
    duration: 1.5,
    location: 'Аудитория 312',
    teacher: 'Проф. Морозов А.В.',
    type: 'lecture',
    color: '#3d52d5'
  },
  {
    id: 2,
    title: 'Базы данных',
    dayIndex: 1,
    startHour: 11,
    duration: 2,
    location: 'Лаборатория 4Б',
    teacher: 'Доц. Сидорова К.И.',
    type: 'practice',
    color: '#2d7a4f'
  },
  {
    id: 3,
    title: 'Английский язык',
    dayIndex: 2,
    startHour: 14,
    duration: 1.5,
    location: 'Онлайн (Zoom)',
    teacher: 'Ст. преп. Фролова О.С.',
    type: 'seminar',
    color: '#0891b2'
  }
])

const form = reactive({
  title: '',
  dayIndex: 0,
  startHour: 9,
  duration: 1.5,
  location: '',
  teacher: '',
  type: 'lecture',
  color: '#3d52d5'
})

function getMonday(d) {
  const date = new Date(d)
  const day = date.getDay()
  const diff = date.getDate() - day + (day === 0 ? -6 : 1)
  return new Date(date.setDate(diff))
}

const days = computed(() => {
  const result = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(currentWeekStart.value)
    date.setDate(date.getDate() + i)
    result.push({
      name: dayNames[i],
      date: date.getDate() + '.' + (date.getMonth() + 1)
    })
  }
  return result
})

const weekLabel = computed(() => {
  const start = currentWeekStart.value
  const end = new Date(start)
  end.setDate(end.getDate() + 6)
  const months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
  return `${start.getDate()} ${months[start.getMonth()]} — ${end.getDate()} ${months[end.getMonth()]} ${end.getFullYear()}`
})

function isToday(dayIndex) {
  const today = new Date()
  const checkDate = new Date(currentWeekStart.value)
  checkDate.setDate(checkDate.getDate() + dayIndex)
  return today.toDateString() === checkDate.toDateString()
}

function prevWeek() {
  const newStart = new Date(currentWeekStart.value)
  newStart.setDate(newStart.getDate() - 7)
  currentWeekStart.value = newStart
}

function nextWeek() {
  const newStart = new Date(currentWeekStart.value)
  newStart.setDate(newStart.getDate() + 7)
  currentWeekStart.value = newStart
}

function getEventsAt(dayIndex, hour) {
  return events.value.filter(e => e.dayIndex === dayIndex && e.startHour === hour)
}

function addAtTime(dayIndex, hour) {
  editingEvent.value = null
  Object.assign(form, {
    title: '',
    dayIndex,
    startHour: hour,
    duration: 1.5,
    location: '',
    teacher: '',
    type: 'lecture',
    color: '#3d52d5'
  })
  showAddModal.value = true
}

function editEvent(event) {
  editingEvent.value = event
  Object.assign(form, { ...event })
  showAddModal.value = true
}

function closeModal() {
  showAddModal.value = false
  editingEvent.value = null
}

function saveEvent() {
  if (!form.title) return

  const endHour = form.startHour + form.duration
  const endTime = `${Math.floor(endHour)}:${(endHour % 1) * 60 || '00'}`

  if (editingEvent.value) {
    const idx = events.value.findIndex(e => e.id === editingEvent.value.id)
    if (idx !== -1) {
      events.value[idx] = {
        ...events.value[idx],
        ...form,
        startTime: `${form.startHour}:00`,
        endTime
      }
    }
  } else {
    events.value.push({
      id: Date.now(),
      ...form,
      startTime: `${form.startHour}:00`,
      endTime
    })
  }

  closeModal()
}

function deleteEvent() {
  if (editingEvent.value) {
    events.value = events.value.filter(e => e.id !== editingEvent.value.id)
    closeModal()
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
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
  transition: all var(--transition);
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
  min-width: 200px;
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
  width: 60px;
  flex-shrink: 0;
  background: var(--surface-2);
}

.time-header {
  height: 50px;
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
  height: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
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
}

.hour-slot {
  height: 60px;
  border-bottom: 1px solid var(--border-soft);
  position: relative;
  cursor: pointer;
  transition: background var(--transition);
}

.hour-slot:hover {
  background: var(--surface-2);
}

.schedule-event {
  position: absolute;
  left: 2px;
  right: 2px;
  top: 2px;
  border-radius: 6px;
  border-left: 3px solid;
  padding: 4px 8px;
  cursor: pointer;
  overflow: hidden;
  z-index: 1;
  transition: transform var(--transition), box-shadow var(--transition);
}

.schedule-event:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow);
}

.event-title {
  font-size: 11px;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 2px;
}

.event-time {
  font-size: 10px;
  color: var(--text-muted);
}

.event-location {
  font-size: 10px;
  color: var(--text-muted);
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
  transform: scale(1.15);
}

.btn-danger {
  color: var(--danger);
}

.btn-danger:hover {
  background: var(--danger-bg);
}
</style>