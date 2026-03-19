<template>
  <div v-if="loading" class="state-card">Загружаем проект…</div>
  <div v-else-if="loadError || !project" class="state-card error">Не удалось открыть проект.</div>
  <div v-else class="project-page">
    <section class="project-hero" :style="heroStyle">
      <div class="hero-copy">
        <div class="hero-badge">{{ isOwner ? 'Владелец проекта' : 'Участник проекта' }}</div>
        <h1>{{ project.name }}</h1>
        <p>{{ project.description || 'Добавь описание проекта, чтобы команда понимала цель и ближайшие шаги.' }}</p>

        <div class="hero-stats">
          <div><strong>{{ project.members?.length || 0 }}</strong><span>участников</span></div>
          <div><strong>{{ openTasks }}</strong><span>открытых задач</span></div>
          <div><strong>{{ project.files?.length || 0 }}</strong><span>файлов</span></div>
        </div>
      </div>

      <div v-if="isOwner" class="hero-settings card">
        <div class="card-title">Параметры проекта</div>
        <div class="form-group">
          <label class="form-label">Название</label>
          <input v-model.trim="projectForm.name" class="input" type="text" />
        </div>
        <div class="form-group">
          <label class="form-label">Описание</label>
          <textarea v-model.trim="projectForm.description" class="textarea" rows="3"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Цвет</label>
          <div class="color-row">
            <button
              v-for="color in colorOptions"
              :key="color"
              type="button"
              class="color-btn"
              :class="{ active: projectForm.color === color }"
              :style="{ background: color }"
              @click="projectForm.color = color"
            />
          </div>
        </div>
        <div class="settings-actions">
          <button class="btn btn-ghost" @click="resetProjectForm">Сбросить</button>
          <button class="btn btn-primary" @click="saveProject">Сохранить</button>
        </div>
      </div>
    </section>

    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </div>

    <section v-if="activeTab === 'tasks'" class="content-grid">
      <div class="card task-form-card">
        <div class="card-header">
          <div>
            <div class="card-title">Новая задача</div>
            <div class="section-sub">Назначай задачи участникам и отслеживай прогресс команды.</div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Название</label>
          <input v-model.trim="taskForm.title" class="input" type="text" placeholder="Например, сверстать главную страницу" />
        </div>
        <div class="form-group">
          <label class="form-label">Описание</label>
          <textarea v-model.trim="taskForm.description" class="textarea" rows="4" placeholder="Что именно нужно сделать"></textarea>
        </div>
        <div class="row-2">
          <div class="form-group">
            <label class="form-label">Срок</label>
            <input v-model="taskForm.due_date" class="input" type="datetime-local" />
          </div>
          <div class="form-group">
            <label class="form-label">Исполнитель</label>
            <select v-model="taskForm.assignee_id" class="input">
              <option value="">Без исполнителя</option>
              <option v-for="member in project.members || []" :key="member.id" :value="String(member.user_id)">
                {{ member.user.name }}
              </option>
            </select>
          </div>
        </div>
        <button class="btn btn-primary wide-btn" @click="createTask">Добавить задачу</button>
      </div>

      <div class="task-list">
        <div v-if="!project.tasks?.length" class="state-card">Пока нет задач. Создай первую задачу для команды.</div>

        <div v-for="task in project.tasks" :key="task.id" class="card task-card">
          <div class="task-head">
            <div>
              <h3>{{ task.title }}</h3>
              <p v-if="task.description">{{ task.description }}</p>
            </div>
            <button class="icon-btn danger" @click="removeTask(task)">×</button>
          </div>

          <div class="task-controls">
            <label>
              <span>Статус</span>
              <select class="input" :value="task.status" @change="changeTaskStatus(task, $event.target.value)">
                <option value="todo">К выполнению</option>
                <option value="in_progress">В работе</option>
                <option value="done">Готово</option>
              </select>
            </label>
            <label>
              <span>Исполнитель</span>
              <select class="input" :value="task.assignee_id ? String(task.assignee_id) : ''" @change="changeTaskAssignee(task, $event.target.value)">
                <option value="">Без исполнителя</option>
                <option v-for="member in project.members || []" :key="member.id" :value="String(member.user_id)">
                  {{ member.user.name }}
                </option>
              </select>
            </label>
            <label>
              <span>Срок</span>
              <input class="input" type="datetime-local" :value="toDateTimeLocal(task.due_date)" @change="changeTaskDueDate(task, $event.target.value)" />
            </label>
          </div>

          <div class="task-footer">
            <span class="task-chip">{{ store.projectTaskStatusLabel(task.status) }}</span>
            <span class="task-meta">
              {{ task.assignee?.name || 'Не назначено' }}
              <template v-if="task.due_date"> · до {{ formatDateTime(task.due_date) }}</template>
            </span>
          </div>
        </div>
      </div>
    </section>

    <section v-else-if="activeTab === 'files'" class="card files-card">
      <div class="card-header files-head">
        <div>
          <div class="card-title">Общие файлы</div>
          <div class="section-sub">Материалы проекта доступны всем участникам команды.</div>
        </div>
        <label class="btn btn-primary upload-btn">
          Загрузить файл
          <input type="file" hidden @change="uploadSharedFile" />
        </label>
      </div>

      <div v-if="!project.files?.length" class="state-card">Общих файлов пока нет.</div>

      <div v-for="file in project.files" :key="file.id" class="file-row">
        <div class="file-icon" :style="{ background: file.icon_bg }">{{ file.icon }}</div>
        <div class="file-copy">
          <strong>{{ file.name }}</strong>
          <span>{{ store.humanSize(file.size_bytes) }} · {{ file.uploader?.name || 'Участник' }}</span>
        </div>
        <div class="file-actions">
          <button class="btn btn-ghost" @click="downloadFile(file)">Скачать</button>
          <button class="btn btn-ghost" @click="removeFile(file)">Удалить</button>
        </div>
      </div>
    </section>

    <section v-else-if="activeTab === 'chat'" class="card chat-card">
      <div class="card-header">
        <div>
          <div class="card-title">Общий чат</div>
          <div class="section-sub">Обсуждайте решения, делитесь прогрессом и фиксируйте договорённости.</div>
        </div>
      </div>

      <div class="chat-feed">
        <div v-if="messagesLoading" class="state-card">Загружаем сообщения…</div>
        <div v-else-if="!messages.length" class="state-card">Чат пуст. Напиши первое сообщение команде.</div>

        <div v-for="message in messages" :key="message.id" class="chat-message">
          <div class="chat-avatar">{{ message.author?.initials || 'WS' }}</div>
          <div class="chat-bubble">
            <div class="chat-meta">
              <strong>{{ message.author?.name || 'Участник' }}</strong>
              <span>{{ formatDateTime(message.created_at) }}</span>
            </div>
            <p>{{ message.body }}</p>
          </div>
        </div>
      </div>

      <div class="chat-compose">
        <textarea v-model.trim="messageDraft" class="textarea" rows="3" placeholder="Напишите сообщение команде"></textarea>
        <button class="btn btn-primary" @click="sendMessage">Отправить</button>
      </div>
    </section>

    <section v-else class="members-grid">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Участники проекта</div>
            <div class="section-sub">Все участники видят общие задачи, файлы и чат проекта.</div>
          </div>
        </div>

        <div v-for="member in project.members" :key="member.id" class="member-row">
          <div class="member-avatar">{{ member.user.initials }}</div>
          <div class="member-copy">
            <strong>{{ member.user.name }}</strong>
            <span>{{ member.user.email || 'Без email' }} · {{ member.role === 'owner' ? 'Владелец' : 'Участник' }}</span>
          </div>
          <button v-if="isOwner && member.role !== 'owner'" class="btn btn-ghost" @click="removeMember(member)">Удалить</button>
        </div>
      </div>

      <div v-if="isOwner" class="card invite-card">
        <div class="card-header">
          <div>
            <div class="card-title">Пригласить участников</div>
            <div class="section-sub">Можно добавить по email или выбрать пользователя через поиск.</div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Добавить по email</label>
          <div class="inline-row">
            <input v-model.trim="inviteEmail" class="input" type="email" placeholder="user@example.com" />
            <button class="btn btn-primary" @click="addByEmail">Добавить</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Поиск пользователя</label>
          <div class="inline-row">
            <input v-model.trim="searchQuery" class="input" type="text" placeholder="Имя или email" @keyup.enter="runSearch" />
            <button class="btn btn-ghost" @click="runSearch">Найти</button>
          </div>
        </div>

        <div v-if="searchResults.length" class="search-results">
          <button v-for="user in searchResults" :key="user.id" class="search-item" @click="addUser(user)">
            <div>
              <strong>{{ user.name }}</strong>
              <span>{{ user.email }}</span>
            </div>
            <span>Добавить</span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { api } from '@/api/index.js'

const route = useRoute()
const store = useWorkspaceStore()
const loading = ref(true)
const loadError = ref(false)
const activeTab = ref('tasks')
const messages = ref([])
const messagesLoading = ref(false)
const messageDraft = ref('')
const inviteEmail = ref('')
const searchQuery = ref('')
const searchResults = ref([])
const taskForm = ref({
  title: '',
  description: '',
  due_date: '',
  assignee_id: '',
})
const projectForm = ref({ name: '', description: '', color: '#7c3aed' })
const colorOptions = ['#7c3aed', '#3d52d5', '#2d7a4f', '#b45309', '#0891b2', '#dc2626']
const tabs = [
  { key: 'tasks', label: 'Задачи' },
  { key: 'files', label: 'Файлы' },
  { key: 'chat', label: 'Чат' },
  { key: 'members', label: 'Участники' },
]

const projectId = computed(() => Number(route.params.id))
const project = computed(() => store.projects.find((item) => item.id === projectId.value))
const isOwner = computed(() => {
  const membership = (project.value?.members || []).find((member) => member.user_id === store.currentUser.id)
  return membership?.role === 'owner'
})
const openTasks = computed(() => (project.value?.tasks || []).filter((task) => task.status !== 'done').length)
const heroStyle = computed(() => ({ '--project-color': project.value?.color || '#7c3aed' }))

watch(project, (value) => {
  if (!value) return
  projectForm.value = {
    name: value.name,
    description: value.description,
    color: value.color,
  }
}, { immediate: true })

watch(() => route.params.id, loadProject, { immediate: true })
watch(activeTab, async (tab) => {
  if (tab === 'chat' && project.value) await loadMessages()
})

async function loadProject() {
  loading.value = true
  loadError.value = false
  try {
    messages.value = []
    await store.fetchProject(projectId.value)
    if (activeTab.value === 'chat') await loadMessages()
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function saveProject() {
  await store.updateProject(projectId.value, { ...projectForm.value })
}

function resetProjectForm() {
  if (!project.value) return
  projectForm.value = {
    name: project.value.name,
    description: project.value.description,
    color: project.value.color,
  }
}

async function createTask() {
  if (!taskForm.value.title) return
  await store.createProjectTask(projectId.value, {
    title: taskForm.value.title,
    description: taskForm.value.description,
    due_date: taskForm.value.due_date || null,
    assignee_id: taskForm.value.assignee_id ? Number(taskForm.value.assignee_id) : null,
    status: 'todo',
  })
  taskForm.value = { title: '', description: '', due_date: '', assignee_id: '' }
}

async function changeTaskStatus(task, status) {
  await store.updateProjectTask(projectId.value, task.id, { status })
}

async function changeTaskAssignee(task, assigneeId) {
  await store.updateProjectTask(projectId.value, task.id, { assignee_id: assigneeId ? Number(assigneeId) : null })
}

async function changeTaskDueDate(task, dueDate) {
  await store.updateProjectTask(projectId.value, task.id, { due_date: dueDate || null })
}

async function removeTask(task) {
  if (!confirm(`Удалить задачу «${task.title}»?`)) return
  await store.deleteProjectTask(projectId.value, task.id)
}

async function uploadSharedFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  await store.uploadProjectFile(projectId.value, file)
  event.target.value = ''
}

async function downloadFile(file) {
  await api.downloadProjectFile(projectId.value, file.id, file.name)
}

async function removeFile(file) {
  if (!confirm(`Удалить файл «${file.name}»?`)) return
  await store.deleteProjectFile(projectId.value, file.id)
}

async function loadMessages() {
  messagesLoading.value = true
  try {
    messages.value = await store.fetchProjectMessages(projectId.value)
  } finally {
    messagesLoading.value = false
  }
}

async function sendMessage() {
  if (!messageDraft.value) return
  const created = await store.postProjectMessage(projectId.value, messageDraft.value)
  messages.value = [...messages.value, created]
  messageDraft.value = ''
}

async function addByEmail() {
  if (!inviteEmail.value) return
  await store.addProjectMember(projectId.value, { email: inviteEmail.value })
  inviteEmail.value = ''
  searchResults.value = []
}

async function runSearch() {
  searchResults.value = await store.searchUsers(searchQuery.value)
}

async function addUser(user) {
  await store.addProjectMember(projectId.value, { user_id: user.id })
  searchResults.value = searchResults.value.filter((item) => item.id !== user.id)
}

async function removeMember(member) {
  if (!confirm(`Удалить ${member.user.name} из проекта?`)) return
  await store.removeProjectMember(projectId.value, member.id)
}

function formatDateTime(value) {
  if (!value) return 'Без срока'
  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function toDateTimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  const tz = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - tz).toISOString().slice(0, 16)
}
</script>

<style scoped>
.state-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 24px;
  text-align: center;
}
.state-card.error { color: var(--danger); }
.project-page { display: grid; gap: 18px; }
.project-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) 360px;
  gap: 18px;
  align-items: start;
}
.hero-copy {
  background: linear-gradient(135deg, color-mix(in srgb, var(--project-color) 15%, white) 0%, white 100%);
  border: 1px solid var(--border);
  border-radius: 26px;
  padding: 26px;
}
.hero-badge {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.85);
  color: var(--project-color);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 14px;
}
.hero-copy h1 {
  font-family: var(--font-display);
  font-size: 34px;
  margin-bottom: 10px;
}
.hero-copy p {
  color: var(--text-secondary);
  max-width: 760px;
}
.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 20px;
}
.hero-stats strong {
  display: block;
  font-size: 26px;
}
.hero-stats span {
  color: var(--text-muted);
  font-size: 12px;
}
.hero-settings { border-radius: 26px; }
.input,
.textarea,
select.input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 11px 13px;
  font: inherit;
  background: var(--surface);
}
.input:focus,
.textarea:focus,
select.input:focus {
  outline: none;
  border-color: var(--accent-mid);
  box-shadow: 0 0 0 3px rgba(61, 82, 213, 0.08);
}
.textarea { resize: vertical; }
.color-row { display: flex; gap: 10px; flex-wrap: wrap; }
.color-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
}
.color-btn.active { border-color: var(--text-primary); transform: scale(1.08); }
.settings-actions { display: flex; justify-content: flex-end; gap: 8px; }
.tabs {
  display: flex;
  gap: 2px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  padding: 3px;
}
.tab {
  flex: 1;
  border: none;
  background: transparent;
  border-radius: 8px;
  padding: 9px 12px;
  cursor: pointer;
  font: inherit;
  color: var(--text-muted);
}
.tab.active {
  background: var(--surface);
  color: var(--text-primary);
  box-shadow: 0 1px 3px rgba(26,23,20,0.08);
}
.content-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}
.task-form-card { position: sticky; top: 12px; }
.section-sub {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 12px;
}
.row-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.wide-btn { width: 100%; justify-content: center; }
.task-list { display: grid; gap: 14px; }
.task-card { display: grid; gap: 14px; }
.task-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
}
.task-head h3 { font-size: 18px; margin-bottom: 6px; }
.task-head p { color: var(--text-secondary); }
.icon-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
}
.icon-btn.danger { color: var(--danger); }
.task-controls {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.task-controls label,
.task-controls span {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}
.task-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}
.task-chip {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-light);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
}
.task-meta { color: var(--text-muted); font-size: 12px; }
.files-card,
.chat-card { display: grid; gap: 14px; }
.files-head { align-items: center; }
.file-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 14px 0;
  border-top: 1px solid var(--border-soft);
}
.file-row:first-of-type { border-top: 0; }
.file-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 20px;
}
.file-copy strong {
  display: block;
  margin-bottom: 4px;
}
.file-copy span { color: var(--text-muted); font-size: 12px; }
.file-actions { display: flex; gap: 8px; }
.chat-feed {
  display: grid;
  gap: 12px;
  max-height: 520px;
  overflow: auto;
  padding-right: 6px;
}
.chat-message {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 12px;
}
.chat-avatar,
.member-avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: var(--accent-light);
  color: var(--accent);
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
}
.chat-bubble {
  background: var(--surface-2);
  border-radius: 18px;
  padding: 14px 16px;
}
.chat-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  margin-bottom: 6px;
}
.chat-meta span { color: var(--text-muted); }
.chat-bubble p { white-space: pre-wrap; }
.chat-compose { display: grid; gap: 10px; }
.members-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 18px;
  align-items: start;
}
.member-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid var(--border-soft);
}
.member-row:first-of-type { border-top: 0; }
.member-copy strong {
  display: block;
  margin-bottom: 3px;
}
.member-copy span {
  color: var(--text-muted);
  font-size: 12px;
}
.inline-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}
.search-results { display: grid; gap: 10px; margin-top: 10px; }
.search-item {
  width: 100%;
  border: 1px solid var(--border-soft);
  background: var(--surface);
  border-radius: 14px;
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  text-align: left;
}
.search-item:hover { background: var(--surface-2); }
.search-item strong { display: block; margin-bottom: 4px; }
.search-item span { color: var(--text-muted); font-size: 12px; }

@media (max-width: 1180px) {
  .project-hero,
  .content-grid,
  .members-grid {
    grid-template-columns: 1fr;
  }
  .task-form-card { position: static; }
}

@media (max-width: 760px) {
  .task-controls,
  .row-2,
  .hero-stats {
    grid-template-columns: 1fr;
  }
  .file-row,
  .member-row,
  .inline-row {
    grid-template-columns: 1fr;
  }
}
</style>
