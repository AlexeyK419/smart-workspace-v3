import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/index.js'

const CURRENT_USER_ID = 1

export const useWorkspaceStore = defineStore('workspace', () => {
  const currentUser = ref({ id: CURRENT_USER_ID, name: 'Алексей Иванов', initials: 'АИ', role: '2-й курс · ИТ' })
  const courses   = ref([])
  const isLoading = ref(false)
  const toast     = ref('')

  const todayEvents = ref([
    { id: 1, time: '09:00', title: 'Лекция: Алгоритмы и СД',  location: 'Аудитория 312',    color: '#3d52d5' },
    { id: 2, time: '11:30', title: 'Практика: Базы данных',     location: 'Лаборатория 4Б',   color: '#2d7a4f' },
    { id: 3, time: '14:00', title: 'Английский язык',           location: 'Онлайн (Zoom)',     color: '#0891b2' },
  ])

  const allAssignments = computed(() => {
    const result = []
    courses.value.forEach((c) => {
      ;(c.assignments || []).forEach((a) => {
        result.push({ ...a, course: c.name, courseColor: c.color })
      })
    })
    return result.sort((a, b) => {
      const parse = (s) => new Date(s.replace(' фев ',' Feb ').replace(' мар ',' Mar ').replace(' янв ',' Jan ').replace(' апр ',' Apr ').replace(' май ',' May ').replace(' июн ',' Jun ').replace(' июл ',' Jul ').replace(' авг ',' Aug ').replace(' сен ',' Sep ').replace(' окт ',' Oct ').replace(' ноя ',' Nov ').replace(' дек ',' Dec '))
      return parse(a.deadline) - parse(b.deadline)
    })
  })

  async function fetchCourses() {
    isLoading.value = true
    try { courses.value = await api.getCourses(CURRENT_USER_ID) }
    catch (e) { showToast('Ошибка загрузки курсов: ' + e.message) }
    finally { isLoading.value = false }
  }

  async function addCourse(payload) {
    try {
      const created = await api.createCourse(CURRENT_USER_ID, payload)
      courses.value.push(created)
      showToast('Курс успешно добавлен!')
      return created
    } catch (e) { showToast('Ошибка: ' + e.message) }
  }

  async function updateCourse(courseId, payload) {
    try {
      const updated = await api.updateCourse(courseId, payload)
      const idx = courses.value.findIndex((c) => c.id === courseId)
      if (idx !== -1) courses.value[idx] = updated
      showToast('Курс обновлён')
      return updated
    } catch (e) { showToast('Ошибка обновления: ' + e.message) }
  }

  async function deleteCourse(courseId) {
    try {
      await api.deleteCourse(courseId)
      courses.value = courses.value.filter((c) => c.id !== courseId)
      showToast('Курс удалён')
    } catch (e) { showToast('Ошибка удаления: ' + e.message) }
  }

  async function uploadMaterial(courseId, file) {
    try {
      const mat = await api.uploadMaterial(courseId, file)
      const course = courses.value.find((c) => c.id === courseId)
      if (course) course.materials = [...(course.materials || []), mat]
      showToast('Файл загружен!')
      return mat
    } catch (e) { showToast('Ошибка загрузки: ' + e.message) }
  }

  async function deleteMaterial(courseId, matId) {
    try {
      await api.deleteMaterial(courseId, matId)
      const course = courses.value.find((c) => c.id === courseId)
      if (course) course.materials = (course.materials || []).filter((m) => m.id !== matId)
      showToast('Материал удалён')
    } catch (e) { showToast('Ошибка: ' + e.message) }
  }

  async function createAssignment(courseId, formData) {
    try {
      const a = await api.createAssignment(courseId, formData)
      const course = courses.value.find((c) => c.id === courseId)
      if (course) course.assignments = [...(course.assignments || []), a]
      showToast('Задание добавлено!')
      return a
    } catch (e) { showToast('Ошибка: ' + e.message) }
  }

  async function updateAssignmentFull(courseId, assignmentId, formData) {
    try {
      const updated = await api.fullUpdateAssignment(courseId, assignmentId, formData)
      const course = courses.value.find((c) => c.id === courseId)
      if (course) {
        const idx = (course.assignments || []).findIndex((a) => a.id === assignmentId)
        if (idx !== -1) course.assignments[idx] = updated
      }
      showToast('Задание обновлено!')
      return updated
    } catch (e) { showToast('Ошибка: ' + e.message) }
  }

  async function updateAssignmentStatus(courseId, assignmentId, status) {
    try {
      const updated = await api.updateAssignment(courseId, assignmentId, { status })
      const course = courses.value.find((c) => c.id === courseId)
      if (course) {
        const idx = (course.assignments || []).findIndex((a) => a.id === assignmentId)
        if (idx !== -1) course.assignments[idx] = updated
      }
    } catch (e) { showToast('Ошибка обновления: ' + e.message) }
  }

  async function deleteAssignment(courseId, assignmentId) {
    try {
      await api.deleteAssignment(courseId, assignmentId)
      const course = courses.value.find((c) => c.id === courseId)
      if (course) course.assignments = (course.assignments || []).filter((a) => a.id !== assignmentId)
      showToast('Задание удалено')
    } catch (e) { showToast('Ошибка: ' + e.message) }
  }

  function showToast(message) {
    toast.value = message
    setTimeout(() => (toast.value = ''), 2800)
  }

  function statusLabel(status) {
    return { pending: 'Ожидает', progress: 'В процессе', done: 'Сдано', overdue: 'Просрочено' }[status] ?? status
  }

  function urgencyClass(deadline) {
    const d = new Date(deadline.replace(' фев ',' Feb ').replace(' мар ',' Mar ').replace(' янв ',' Jan ').replace(' апр ',' Apr ').replace(' май ',' May ').replace(' июн ',' Jun ').replace(' июл ',' Jul ').replace(' авг ',' Aug ').replace(' сен ',' Sep ').replace(' окт ',' Oct ').replace(' ноя ',' Nov ').replace(' дек ',' Dec '))
    const diff = (d - Date.now()) / (1000 * 60 * 60 * 24)
    if (diff < 0) return 'deadline-overdue'
    if (diff < 5) return 'deadline-soon'
    return 'deadline-ok'
  }

  function humanSize(bytes) {
    if (bytes < 1024)    return bytes + ' Б'
    if (bytes < 1048576) return (bytes/1024).toFixed(0) + ' КБ'
    return (bytes/1048576).toFixed(1) + ' МБ'
  }

  return {
    currentUser, courses, isLoading, toast, todayEvents, allAssignments,
    fetchCourses, addCourse, updateCourse, deleteCourse,
    uploadMaterial, deleteMaterial,
    createAssignment, updateAssignmentFull, updateAssignmentStatus, deleteAssignment,
    showToast, statusLabel, urgencyClass, humanSize,
  }
})