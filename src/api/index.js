const BASE = 'http://localhost:8000'
const TOKEN_KEY = 'workspace_token'

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


function getFilenameFromDisposition(header) {
  const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(header || '')
  const raw = match?.[1] || match?.[2] || ''
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
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

async function request(method, path, body = null) {
  const opts = { method, headers: {} }

  if (authToken) {
    opts.headers.Authorization = `Bearer ${authToken}`
  }

  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  } else if (body instanceof FormData) {
    opts.body = body
  }

  const res = await fetch(`${BASE}${path}`, opts)
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
  getCourses:     () => request('GET', '/users/me/courses'),

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
  deleteMaterial:      (courseId, matId) => request('DELETE', `/courses/${courseId}/materials/${matId}`),
  downloadMaterial:     (courseId, matId, fileName = 'material') => downloadWithAuth(`/courses/${courseId}/materials/${matId}/download`, fileName),

  getAssignments:       (courseId)         => request('GET',   `/courses/${courseId}/assignments/`),
  createAssignment:     (courseId, fd)     => request('POST',  `/courses/${courseId}/assignments/`, fd),
  updateAssignment:     (courseId, id, data) => request('PATCH', `/courses/${courseId}/assignments/${id}`, data),
  fullUpdateAssignment: (courseId, id, fd) => request('PUT', `/courses/${courseId}/assignments/${id}`, fd),
  deleteAssignment:      (courseId, id)      => request('DELETE', `/courses/${courseId}/assignments/${id}`),
  downloadAssignment:    (courseId, id, fileName = 'assignment') => downloadWithAuth(`/courses/${courseId}/assignments/${id}/download`, fileName),

  getSchedule:       ()         => request('GET',   '/schedule/'),
  createSchedule:    (data)     => request('POST',  '/schedule/', data),
  updateSchedule:    (id, data) => request('PATCH', `/schedule/${id}`, data),
  deleteSchedule:    (id)       => request('DELETE', `/schedule/${id}`),

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

  aiModels: () => request('GET', '/ai/models'),
}
