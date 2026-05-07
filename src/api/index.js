const BASE = 'http://localhost:8000'
const TOKEN_KEY = 'workspace_token'
const DEFAULT_TIMEOUT_MS = 15000
const AI_TIMEOUT_MS = 45000

let authToken = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) || '' : ''

export function setAuthToken(token) {
  authToken = token || ''
  if (typeof window !== 'undefined') {
    if (authToken) localStorage.setItem(TOKEN_KEY, authToken)
    else localStorage.removeItem(TOKEN_KEY)
  }
}

export function getAuthToken() {
  return authToken
}

function toWebSocketBase(url) {
  return url.replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:')
}

function getFilenameFromDisposition(header) {
  const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(header || '')
  const raw = match?.[1] || match?.[2] || ''
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
}

export async function fetchBlobUrl(path) {
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}
  const res = await fetch(`${BASE}${path}`, { headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Ошибка загрузки')
  }
  const blob = await res.blob()
  return window.URL.createObjectURL(blob)
}

export function getDownloadPath(entityType, courseId, projectId, fileId) {
  if (entityType === 'material') return `/courses/${courseId}/materials/${fileId}/download`
  if (entityType === 'assignment') return `/courses/${courseId}/assignments/${fileId}/download`
  if (entityType === 'assignmentFile' || entityType === 'assignment_file')
    return `/courses/${courseId}/assignments/${projectId}/files/${fileId}/download`
  if (entityType === 'projectFile') return `/projects/${projectId}/files/${fileId}/download`
  return null
}

export async function downloadWithAuth(path, fallbackName = 'download') {
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}
  const res = await fetch(`${BASE}${path}`, { headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Ошибка скачивания')
  }

  const blob = await res.blob()
  const fileName = getFilenameFromDisposition(res.headers.get('Content-Disposition')) || fallbackName
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function resolveTimeout(path) {
  return path.startsWith('/ai/') ? AI_TIMEOUT_MS : DEFAULT_TIMEOUT_MS
}

async function request(method, path, body = null) {
  const opts = { method, headers: {} }
  const controller = new AbortController()
  const timeoutMs = resolveTimeout(path)
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
  opts.signal = controller.signal

  if (authToken) {
    opts.headers.Authorization = `Bearer ${authToken}`
  }

  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  } else if (body instanceof FormData) {
    opts.body = body
  }

  let res
  try {
    res = await fetch(`${BASE}${path}`, opts)
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error('Превышено время ожидания ответа сервера')
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API error')
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  register: (data) => request('POST', '/auth/register', data),
  login:    (data) => request('POST', '/auth/login', data),
  me:       ()     => request('GET',  '/auth/me'),
  logout:   ()     => request('POST', '/auth/logout'),

  getCurrentUser: () => request('GET', '/users/me'),
  updateCurrentUser: (data) => request('PATCH', '/users/me', data),
  updatePassword: (data) => request('POST', '/users/me/password', data),
  getCourses:     () => request('GET', '/users/me/courses'),
  searchUsers:    (query) => request('GET', `/users/search?q=${encodeURIComponent(query)}`),

  getChats:        () => request('GET', '/chats/'),
  getChat:         (chatId) => request('GET', `/chats/${chatId}`),
  createDirectChat: (data) => request('POST', '/chats/', data),
  getChatMessages: (chatId) => request('GET', `/chats/${chatId}/messages`),
  postChatMessage: (chatId, data) => request('POST', `/chats/${chatId}/messages`, data),
  markChatRead:    (chatId) => request('POST', `/chats/${chatId}/read`),
  chatsSocketUrl:  () => {
    const token = encodeURIComponent(authToken || '')
    return `${toWebSocketBase(BASE)}/ws/chats/?token=${token}`
  },

  getCourse:     (id)   => request('GET',    `/courses/${id}`),
  createCourse:  (data) => request('POST',   '/courses/', data),
  updateCourse:  (id, data) => request('PATCH', `/courses/${id}`, data),
  deleteCourse:  (id)   => request('DELETE', `/courses/${id}`),

  getMaterials:  (courseId) => request('GET', `/courses/${courseId}/materials/`),
  uploadMaterial: (courseId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('POST', `/courses/${courseId}/materials/`, fd)
  },
  deleteMaterial:       (courseId, matId) => request('DELETE', `/courses/${courseId}/materials/${matId}`),
  downloadMaterial:     (courseId, matId, fileName = 'material') => downloadWithAuth(`/courses/${courseId}/materials/${matId}/download`, fileName),
  previewMaterial:      (courseId, matId) => request('GET', `/courses/${courseId}/materials/${matId}/preview`),

  getAssignments:       (courseId)           => request('GET',   `/courses/${courseId}/assignments/`),
  createAssignment:     (courseId, fd)       => request('POST',  `/courses/${courseId}/assignments/`, fd),
  updateAssignment:     (courseId, id, data) => request('PATCH', `/courses/${courseId}/assignments/${id}`, data),
  fullUpdateAssignment: (courseId, id, fd)   => request('PUT',   `/courses/${courseId}/assignments/${id}`, fd),
  deleteAssignment:     (courseId, id)       => request('DELETE', `/courses/${courseId}/assignments/${id}`),
  downloadAssignment:   (courseId, id, fileName = 'assignment') => downloadWithAuth(`/courses/${courseId}/assignments/${id}/download`, fileName),
  previewAssignment:    (courseId, id) => request('GET', `/courses/${courseId}/assignments/${id}/preview`),

  uploadAssignmentFile: (courseId, assignmentId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('POST', `/courses/${courseId}/assignments/${assignmentId}/files`, fd)
  },
  downloadAssignmentFile: (courseId, assignmentId, fileId, fileName = 'file') =>
    downloadWithAuth(`/courses/${courseId}/assignments/${assignmentId}/files/${fileId}/download`, fileName),
  previewAssignmentFile: (courseId, assignmentId, fileId) =>
    request('GET', `/courses/${courseId}/assignments/${assignmentId}/files/${fileId}/preview`),
  deleteAssignmentFile:  (courseId, assignmentId, fileId) =>
    request('DELETE', `/courses/${courseId}/assignments/${assignmentId}/files/${fileId}`),

  getSchedule:    ()         => request('GET',    '/schedule/'),
  createSchedule: (data)     => request('POST',   '/schedule/', data),
  updateSchedule: (id, data) => request('PATCH',  `/schedule/${id}`, data),
  deleteSchedule: (id)       => request('DELETE', `/schedule/${id}`),

  getProjects:       ()              => request('GET', '/projects/'),
  getProject:        (id)            => request('GET', `/projects/${id}`),
  createProject:     (data)          => request('POST', '/projects/', data),
  updateProject:     (id, data)      => request('PATCH', `/projects/${id}`, data),
  deleteProject:     (id)            => request('DELETE', `/projects/${id}`),
  addProjectMember:  (projectId, data) => request('POST', `/projects/${projectId}/members`, data),
  removeProjectMember: (projectId, memberId) => request('DELETE', `/projects/${projectId}/members/${memberId}`),
  createProjectTask: (projectId, data) => request('POST', `/projects/${projectId}/tasks`, data),
  updateProjectTask: (projectId, taskId, data) => request('PATCH', `/projects/${projectId}/tasks/${taskId}`, data),
  deleteProjectTask: (projectId, taskId) => request('DELETE', `/projects/${projectId}/tasks/${taskId}`),
  createProjectTaskComment: (projectId, taskId, data) => request('POST', `/projects/${projectId}/tasks/${taskId}/comments`, data),
  getProjectMessages: (projectId) => request('GET', `/projects/${projectId}/messages`),
  postProjectMessage: (projectId, data) => request('POST', `/projects/${projectId}/messages`, data),
  projectChatSocketUrl: (projectId) => {
    const token = encodeURIComponent(authToken || '')
    return `${toWebSocketBase(BASE)}/ws/projects/${projectId}/chat?token=${token}`
  },
  getProjectFiles:    (projectId) => request('GET', `/projects/${projectId}/files`),
  uploadProjectFile:  (projectId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('POST', `/projects/${projectId}/files`, fd)
  },
  deleteProjectFile:  (projectId, fileId) => request('DELETE', `/projects/${projectId}/files/${fileId}`),
  downloadProjectFile: (projectId, fileId, fileName = 'project-file') => downloadWithAuth(`/projects/${projectId}/files/${fileId}/download`, fileName),
  previewProjectFile:  (projectId, fileId) => request('GET', `/projects/${projectId}/files/${fileId}/preview`),

  aiChat: (messages, opts = {}) =>
    request('POST', '/ai/chat', {
      messages,
      temperature: opts.temperature ?? 0.7,
      max_tokens: opts.max_tokens ?? 1024,
    }),

  aiGeneratePlan: (courseId, extraContext = '') =>
    request('POST', `/ai/courses/${courseId}/plan`, { extra_context: extraContext }),

  aiAssignmentHelp: (assignmentId, question = '') =>
    request('POST', `/ai/assignments/${assignmentId}/help`, { question }),

  aiWorkspaceSummary: () =>
    request('POST', '/ai/workspace/summary'),

  aiProjectSummary: (projectId) =>
    request('POST', `/ai/projects/${projectId}/summary`),

  aiModels: () => request('GET', '/ai/models'),
}
