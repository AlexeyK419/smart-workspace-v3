const BASE = 'http://localhost:8000'

async function request(method, path, body = null) {
  const opts = { method, headers: {} }
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
  getUser:    (id)   => request('GET',  `/users/${id}`),
  listUsers:  ()     => request('GET',  '/users/'),
  createUser: (data) => request('POST', '/users/', data),

  getCourses:    (userId)       => request('GET',    `/users/${userId}/courses`),
  getCourse:     (id)           => request('GET',    `/courses/${id}`),
  createCourse:  (userId, data) => request('POST',   `/courses/?user_id=${userId}`, data),
  updateCourse:  (id, data)     => request('PATCH',  `/courses/${id}`, data),
  deleteCourse:  (id)           => request('DELETE', `/courses/${id}`),

  getMaterials:  (courseId) => request('GET', `/courses/${courseId}/materials/`),
  uploadMaterial: (courseId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('POST', `/courses/${courseId}/materials/`, fd)
  },
  deleteMaterial:      (courseId, matId) => request('DELETE', `/courses/${courseId}/materials/${matId}`),
  downloadMaterialUrl: (courseId, matId) => `${BASE}/courses/${courseId}/materials/${matId}/download`,

  getAssignments:    (courseId)           => request('GET',   `/courses/${courseId}/assignments/`),
  createAssignment:  (courseId, fd)       => request('POST',  `/courses/${courseId}/assignments/`, fd),
  updateAssignment:  (courseId, id, data) => request('PATCH', `/courses/${courseId}/assignments/${id}`, data),
  fullUpdateAssignment: (courseId, id, fd) =>
    request('PUT', `/courses/${courseId}/assignments/${id}`, fd),
  deleteAssignment:  (courseId, id) => request('DELETE', `/courses/${courseId}/assignments/${id}`),
  downloadAssignmentUrl: (courseId, id) => `${BASE}/courses/${courseId}/assignments/${id}/download`,

  getSchedule:       (userId)             => request('GET',   `/users/${userId}/schedule/`),
  createSchedule:    (userId, data)       => request('POST',  `/users/${userId}/schedule/`, data),
  updateSchedule:    (userId, id, data)   => request('PATCH', `/users/${userId}/schedule/${id}`, data),
  deleteSchedule:    (userId, id)         => request('DELETE', `/users/${userId}/schedule/${id}`),

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
