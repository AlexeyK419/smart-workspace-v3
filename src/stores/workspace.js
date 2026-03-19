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

function normalizeProjectTask(task) {
  return {
    ...task,
    dueDate: task?.due_date ? new Date(task.due_date) : null,
  }
}

function normalizeProject(project) {
  return {
    ...project,
    tasks: [...(project.tasks || [])]
      .map(normalizeProjectTask)
      .sort((a, b) => {
        const aTime = a.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
        const bTime = b.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
        return aTime - bTime
      }),
    files: [...(project.files || [])].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
    members: [...(project.members || [])].sort((a, b) => {
      if (a.role === b.role) return a.user.name.localeCompare(b.user.name, 'ru')
      return a.role === 'owner' ? -1 : 1
    }),
  }
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const authStore = useAuthStore()
  const courses = ref([])
  const scheduleEvents = ref([])
  const projects = ref([])
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

  const projectTasks = computed(() => {
    const items = []
    projects.value.forEach((project) => {
      ;(project.tasks || []).forEach((task) => {
        items.push({
          ...task,
          projectId: project.id,
          projectName: project.name,
          projectColor: project.color,
        })
      })
    })
    return items.sort((a, b) => {
      const aTime = a.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
      const bTime = b.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
      return aTime - bTime
    })
  })

  const pendingProjectTasks = computed(() =>
    projectTasks.value.filter((task) => task.status !== 'done')
  )

  function replaceProject(project) {
    const normalized = normalizeProject(project)
    const idx = projects.value.findIndex((item) => item.id === normalized.id)
    if (idx === -1) projects.value.unshift(normalized)
    else projects.value[idx] = normalized
    projects.value = [...projects.value].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    return normalized
  }

  function resetWorkspace() {
    courses.value = []
    scheduleEvents.value = []
    projects.value = []
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

  async function fetchProjects() {
    if (!authStore.isAuthenticated) {
      projects.value = []
      return
    }

    try {
      projects.value = (await api.getProjects()).map(normalizeProject)
    } catch (e) {
      showToast('Ошибка загрузки проектов: ' + e.message)
    }
  }

  async function fetchProject(projectId) {
    try {
      return replaceProject(await api.getProject(projectId))
    } catch (e) {
      showToast('Ошибка загрузки проекта: ' + e.message)
      throw e
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

  async function createProject(payload) {
    try {
      const created = await api.createProject(payload)
      const normalized = replaceProject(created)
      showToast('Проект создан')
      return normalized
    } catch (e) {
      showToast('Ошибка создания проекта: ' + e.message)
      throw e
    }
  }

  async function updateProject(projectId, payload) {
    try {
      const updated = replaceProject(await api.updateProject(projectId, payload))
      showToast('Проект обновлён')
      return updated
    } catch (e) {
      showToast('Ошибка обновления проекта: ' + e.message)
      throw e
    }
  }

  async function deleteProject(projectId) {
    try {
      await api.deleteProject(projectId)
      projects.value = projects.value.filter((project) => project.id !== projectId)
      showToast('Проект удалён')
    } catch (e) {
      showToast('Ошибка удаления проекта: ' + e.message)
      throw e
    }
  }

  async function searchUsers(query) {
    if (!query?.trim()) return []
    try {
      return await api.searchUsers(query.trim())
    } catch (e) {
      showToast('Ошибка поиска пользователей: ' + e.message)
      return []
    }
  }

  async function addProjectMember(projectId, payload) {
    try {
      const project = replaceProject(await api.addProjectMember(projectId, payload))
      showToast('Участник добавлен')
      return project
    } catch (e) {
      showToast('Ошибка добавления участника: ' + e.message)
      throw e
    }
  }

  async function removeProjectMember(projectId, memberId) {
    try {
      const project = replaceProject(await api.removeProjectMember(projectId, memberId))
      showToast('Участник удалён')
      return project
    } catch (e) {
      showToast('Ошибка удаления участника: ' + e.message)
      throw e
    }
  }

  async function createProjectTask(projectId, payload) {
    try {
      const task = normalizeProjectTask(await api.createProjectTask(projectId, payload))
      const project = projects.value.find((item) => item.id === projectId)
      if (project) {
        project.tasks = [...(project.tasks || []), task].sort((a, b) => {
          const aTime = a.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
          const bTime = b.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
          return aTime - bTime
        })
      }
      showToast('Задача добавлена')
      return task
    } catch (e) {
      showToast('Ошибка создания задачи: ' + e.message)
      throw e
    }
  }

  async function updateProjectTask(projectId, taskId, payload) {
    try {
      const updated = normalizeProjectTask(await api.updateProjectTask(projectId, taskId, payload))
      const project = projects.value.find((item) => item.id === projectId)
      if (project) {
        const idx = (project.tasks || []).findIndex((task) => task.id === taskId)
        if (idx !== -1) project.tasks[idx] = updated
        project.tasks = [...(project.tasks || [])].sort((a, b) => {
          const aTime = a.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
          const bTime = b.dueDate?.getTime?.() ?? Number.POSITIVE_INFINITY
          return aTime - bTime
        })
      }
      showToast('Задача обновлена')
      return updated
    } catch (e) {
      showToast('Ошибка обновления задачи: ' + e.message)
      throw e
    }
  }

  async function deleteProjectTask(projectId, taskId) {
    try {
      await api.deleteProjectTask(projectId, taskId)
      const project = projects.value.find((item) => item.id === projectId)
      if (project) project.tasks = (project.tasks || []).filter((task) => task.id !== taskId)
      showToast('Задача удалена')
    } catch (e) {
      showToast('Ошибка удаления задачи: ' + e.message)
      throw e
    }
  }

  async function uploadProjectFile(projectId, file) {
    try {
      const uploaded = await api.uploadProjectFile(projectId, file)
      const project = projects.value.find((item) => item.id === projectId)
      if (project) project.files = [uploaded, ...(project.files || [])]
      showToast('Файл проекта загружен')
      return uploaded
    } catch (e) {
      showToast('Ошибка загрузки файла: ' + e.message)
      throw e
    }
  }

  async function deleteProjectFile(projectId, fileId) {
    try {
      await api.deleteProjectFile(projectId, fileId)
      const project = projects.value.find((item) => item.id === projectId)
      if (project) project.files = (project.files || []).filter((file) => file.id !== fileId)
      showToast('Файл удалён')
    } catch (e) {
      showToast('Ошибка удаления файла: ' + e.message)
      throw e
    }
  }

  async function fetchProjectMessages(projectId) {
    try {
      return await api.getProjectMessages(projectId)
    } catch (e) {
      showToast('Ошибка загрузки чата: ' + e.message)
      throw e
    }
  }

  async function postProjectMessage(projectId, body) {
    try {
      const message = await api.postProjectMessage(projectId, { body })
      showToast('Сообщение отправлено')
      return message
    } catch (e) {
      showToast('Ошибка отправки сообщения: ' + e.message)
      throw e
    }
  }

  function showToast(message) {
    toast.value = message
    setTimeout(() => {
      if (toast.value === message) toast.value = ''
    }, 2800)
  }

  function statusLabel(status) {
    return { pending: 'Ожидает', progress: 'В процессе', done: 'Сдано', overdue: 'Просрочено' }[status] ?? status
  }

  function projectTaskStatusLabel(status) {
    return { todo: 'К выполнению', in_progress: 'В работе', done: 'Готово' }[status] ?? status
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
    projects,
    isLoading,
    toast,
    allAssignments,
    todayEvents,
    projectTasks,
    pendingProjectTasks,
    fetchCourses,
    fetchSchedule,
    fetchProjects,
    fetchProject,
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
    createProject,
    updateProject,
    deleteProject,
    searchUsers,
    addProjectMember,
    removeProjectMember,
    createProjectTask,
    updateProjectTask,
    deleteProjectTask,
    uploadProjectFile,
    deleteProjectFile,
    fetchProjectMessages,
    postProjectMessage,
    showToast,
    statusLabel,
    projectTaskStatusLabel,
    urgencyClass,
    humanSize,
  }
})
