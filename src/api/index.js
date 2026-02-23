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
  // ── Users ────────────────────────────────────────────────
  getUser:    (id)   => request('GET',  `/users/${id}`),
  listUsers:  ()     => request('GET',  '/users/'),
  createUser: (data) => request('POST', '/users/', data),

  // ── Courses ───────────────────────────────────────────────
  getCourses:   (userId) => request('GET',    `/users/${userId}/courses`),
  createCourse: (userId, data) => request('POST', `/courses/?user_id=${userId}`, data),
  updateCourse: (id, data)     => request('PATCH', `/courses/${id}`, data),
  deleteCourse: (id)           => request('DELETE', `/courses/${id}`),

  // ── Materials ─────────────────────────────────────────────
  getMaterials:   (courseId) => request('GET', `/courses/${courseId}/materials/`),
  uploadMaterial: (courseId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('POST', `/courses/${courseId}/materials/`, fd)
  },
  deleteMaterial:      (courseId, matId) => request('DELETE', `/courses/${courseId}/materials/${matId}`),
  downloadMaterialUrl: (courseId, matId) => `${BASE}/courses/${courseId}/materials/${matId}/download`,

  // ── Assignments ───────────────────────────────────────────
  getAssignments:      (courseId) => request('GET', `/courses/${courseId}/assignments/`),
  createAssignment:    (courseId, fd) => request('POST', `/courses/${courseId}/assignments/`, fd),
  updateAssignment:    (courseId, id, data) => request('PATCH', `/courses/${courseId}/assignments/${id}`, data),
  deleteAssignment:    (courseId, id) => request('DELETE', `/courses/${courseId}/assignments/${id}`),
  downloadAssignmentUrl: (courseId, id) => `${BASE}/courses/${courseId}/assignments/${id}/download`,

  // ── AI / GigaChat ─────────────────────────────────────────
  /**
   * General chat. messages = [{role:'user'|'assistant', content:string}]
   */
  aiChat: (messages, opts = {}) =>
    request('POST', '/ai/chat', {
      messages,
      temperature: opts.temperature ?? 0.7,
      max_tokens:  opts.max_tokens  ?? 1024,
    }),

  /**
   * Generate a study plan for a course.
   */
  aiGeneratePlan: (courseId, extraContext = '') =>
    request('POST', `/ai/courses/${courseId}/plan`, { extra_context: extraContext }),

  /**
   * Get structured advice for a specific assignment.
   */
  aiAssignmentHelp: (assignmentId, question = '') =>
    request('POST', `/ai/assignments/${assignmentId}/help`, { question }),

  /**
   * List available GigaChat models.
   */
  aiModels: () => request('GET', '/ai/models'),
}
