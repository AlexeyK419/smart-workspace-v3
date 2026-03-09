import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/index.js'
import { useAuthStore } from '@/stores/auth'
import { parseRuDate, formatTimeFromMinutes, currentDayIndex } from '@/utils/dates'

function normalizeScheduleEvent(event) {
  const startMinute = Number(event.start_minute)
  const durationMinutes = Number(event.duration_minutes)

  return {
    ...event,
    dayIndex: Number(event.day_index),
    startMinute,
    durationMinutes,
    startTime: formatTimeFromMinutes(startMinute),
    endTime: formatTimeFromMinutes(startMinute + durationMinutes),
  }
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const authStore = useAuthStore()
  const courses = ref([])
  const scheduleEvents = ref([])
  const isLoading = ref(false)
  const toast = ref('')

  const currentUser = computed(() => authStore.currentUser || {
    id: null,
    name: 'Гость',
    initials: 'GS',
    role: 'Студент',
  })

  const allAssignments = computed(() => {
    const result = []
    courses.value.forEach((course) => {
      ;(course.assignments || []).forEach((assignment) => {
        const deadlineDate = assignment.deadline_dt
          ? new Date(assignment.deadline_dt)
          : parseRuDate(assignment.deadline)

        result.push({
          ...assignment,
          course: course.name,
          courseId: course.id,
          courseColor: course.color,
          deadlineDate,
        })
      })
    })

    return result.sort((a, b) => {
      const aTime = a.deadlineDate?.getTime?.() ?? Number.POSITIVE_INFINITY
      const bTime = b.deadlineDate?.getTime?.() ?? Number.POSITIVE_INFINITY
      return aTime - bTime
    })
  })

  const todayEvents = computed(() => {
    const todayIndex = currentDayIndex()
    return scheduleEvents.value
      .filter((event) => event.dayIndex === todayIndex)
      .sort((a, b) => a.startMinute - b.startMinute)
      .map((event) => ({
        ...event,
        time: event.startTime,
      }))
  })

  function resetWorkspace() {
    courses.value = []
    scheduleEvents.value = []
  }

  async function fetchCourses() {
    if (!authStore.isAuthenticated) {
      courses.value = []
      return
    }

    isLoading.value = true
    try {
      courses.value = await api.getCourses()
    } catch (e) {
      showToast('Ошибка загрузки курсов: ' + e.message)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchSchedule() {
    if (!authStore.isAuthenticated) {
      scheduleEvents.value = []
      return
    }

    try {
      const events = await api.getSchedule()
      scheduleEvents.value = events.map(normalizeScheduleEvent)
    } catch (e) {
      showToast('Ошибка загрузки расписания: ' + e.message)
    }
  }

  async function addCourse(payload) {
    try {
      const created = await api.createCourse(payload)
      courses.value.push(created)
      showToast('Курс успешно добавлен!')
      return created
    } catch (e) {
      showToast('Ошибка: ' + e.message)
    }
  }

  async function updateCourse(courseId, payload) {
    try {
      const updated = await api.updateCourse(courseId, payload)
      const idx = courses.value.findIndex((course) => course.id === courseId)
      if (idx !== -1) courses.value[idx] = updated
      showToast('Курс обновлён')
      return updated
    } catch (e) {
      showToast('Ошибка обновления: ' + e.message)
    }
  }

  async function deleteCourse(courseId) {
    try {
      await api.deleteCourse(courseId)
      courses.value = courses.value.filter((course) => course.id !== courseId)
      showToast('Курс удалён')
    } catch (e) {
      showToast('Ошибка удаления: ' + e.message)
    }
  }

  async function uploadMaterial(courseId, file) {
    try {
      const material = await api.uploadMaterial(courseId, file)
      const course = courses.value.find((item) => item.id === courseId)
      if (course) course.materials = [...(course.materials || []), material]
      showToast('Файл загружен!')
      return material
    } catch (e) {
      showToast('Ошибка загрузки: ' + e.message)
    }
  }

  async function deleteMaterial(courseId, materialId) {
    try {
      await api.deleteMaterial(courseId, materialId)
      const course = courses.value.find((item) => item.id === courseId)
      if (course) course.materials = (course.materials || []).filter((material) => material.id !== materialId)
      showToast('Материал удалён')
    } catch (e) {
      showToast('Ошибка: ' + e.message)
    }
  }

  async function createAssignment(courseId, formData) {
    try {
      const assignment = await api.createAssignment(courseId, formData)
      const course = courses.value.find((item) => item.id === courseId)
      if (course) course.assignments = [...(course.assignments || []), assignment]
      showToast('Задание добавлено!')
      return assignment
    } catch (e) {
      showToast('Ошибка: ' + e.message)
    }
  }

  async function updateAssignmentFull(courseId, assignmentId, formData) {
    try {
      const updated = await api.fullUpdateAssignment(courseId, assignmentId, formData)
      const course = courses.value.find((item) => item.id === courseId)
      if (course) {
        const idx = (course.assignments || []).findIndex((assignment) => assignment.id === assignmentId)
        if (idx !== -1) course.assignments[idx] = updated
      }
      showToast('Задание обновлено!')
      return updated
    } catch (e) {
      showToast('Ошибка: ' + e.message)
    }
  }

  async function updateAssignmentStatus(courseId, assignmentId, status) {
    try {
      const updated = await api.updateAssignment(courseId, assignmentId, { status })
      const course = courses.value.find((item) => item.id === courseId)
      if (course) {
        const idx = (course.assignments || []).findIndex((assignment) => assignment.id === assignmentId)
        if (idx !== -1) course.assignments[idx] = updated
      }
    } catch (e) {
      showToast('Ошибка обновления: ' + e.message)
    }
  }

  async function deleteAssignment(courseId, assignmentId) {
    try {
      await api.deleteAssignment(courseId, assignmentId)
      const course = courses.value.find((item) => item.id === courseId)
      if (course) course.assignments = (course.assignments || []).filter((assignment) => assignment.id !== assignmentId)
      showToast('Задание удалено')
    } catch (e) {
      showToast('Ошибка: ' + e.message)
    }
  }

  async function createScheduleEvent(payload) {
    try {
      const created = await api.createSchedule(payload)
      const normalized = normalizeScheduleEvent(created)
      scheduleEvents.value = [...scheduleEvents.value, normalized].sort((a, b) => (
        a.dayIndex - b.dayIndex || a.startMinute - b.startMinute
      ))
      showToast('Занятие добавлено')
      return normalized
    } catch (e) {
      showToast('Ошибка сохранения занятия: ' + e.message)
    }
  }

  async function updateScheduleEvent(eventId, payload) {
    try {
      const updated = normalizeScheduleEvent(await api.updateSchedule(eventId, payload))
      const idx = scheduleEvents.value.findIndex((event) => event.id === eventId)
      if (idx !== -1) scheduleEvents.value[idx] = updated
      scheduleEvents.value = [...scheduleEvents.value].sort((a, b) => (
        a.dayIndex - b.dayIndex || a.startMinute - b.startMinute
      ))
      showToast('Занятие обновлено')
      return updated
    } catch (e) {
      showToast('Ошибка обновления занятия: ' + e.message)
    }
  }

  async function deleteScheduleEvent(eventId) {
    try {
      await api.deleteSchedule(eventId)
      scheduleEvents.value = scheduleEvents.value.filter((event) => event.id !== eventId)
      showToast('Занятие удалено')
    } catch (e) {
      showToast('Ошибка удаления занятия: ' + e.message)
    }
  }

  function showToast(message) {
    toast.value = message
    setTimeout(() => (toast.value = ''), 2800)
  }

  function statusLabel(status) {
    return { pending: 'Ожидает', progress: 'В процессе', done: 'Сдано', overdue: 'Просрочено' }[status] ?? status
  }

  function urgencyClass(deadline) {
    const date = parseRuDate(deadline) ?? new Date(deadline)
    if (Number.isNaN(date?.getTime?.())) return 'deadline-ok'
    const diff = (date.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    if (diff < 0) return 'deadline-overdue'
    if (diff < 5) return 'deadline-soon'
    return 'deadline-ok'
  }

  function humanSize(bytes) {
    if (bytes < 1024) return bytes + ' Б'
    if (bytes < 1048576) return (bytes / 1024).toFixed(0) + ' КБ'
    return (bytes / 1048576).toFixed(1) + ' МБ'
  }

  return {
    currentUser,
    courses,
    scheduleEvents,
    isLoading,
    toast,
    allAssignments,
    todayEvents,
    fetchCourses,
    fetchSchedule,
    resetWorkspace,
    addCourse,
    updateCourse,
    deleteCourse,
    uploadMaterial,
    deleteMaterial,
    createAssignment,
    updateAssignmentFull,
    updateAssignmentStatus,
    deleteAssignment,
    createScheduleEvent,
    updateScheduleEvent,
    deleteScheduleEvent,
    showToast,
    statusLabel,
    urgencyClass,
    humanSize,
  }
})
