<template>
  <div v-if="loading" class="state-card">Загружаем проект…</div>
  <div v-else-if="loadError || !project" class="state-card error">Не удалось открыть проект.</div>
  <div v-else class="project-page">
    <section class="project-hero" :style="heroStyle">
      <div class="hero-copy">
        <button
          v-if="isOwner"
          class="btn btn-primary hero-edit-btn"
          @click="openProjectEditModal"
        >
          Редактировать
        </button>
        <div class="hero-badge">{{ isOwner ? 'Владелец проекта' : 'Участник проекта' }}</div>
        <h1>{{ project.name }}</h1>
        <p>{{ project.description || 'Добавь описание проекта, чтобы команда понимала цель, сроки и ближайшие шаги.' }}</p>

        <div class="hero-stats">
          <div>
            <strong>{{ formatCountRu(project.members?.length || 0, 'участник', 'участника', 'участников') }}</strong>
          </div>
          <div>
            <strong>{{ formatCountRu(openTasks, 'активная задача', 'активные задачи', 'активных задач') }}</strong>
          </div>
          <div>
            <strong>{{ formatCountRu(doneTasks, 'закрытая задача', 'закрытые задачи', 'закрытых задач') }}</strong>
          </div>
        </div>

        <div class="hero-inline-metrics">
          <div class="metric-pill">
            <span class="metric-label">Ближайший дедлайн</span>
            <strong>{{ nextDeadlineTask ? `${nextDeadlineTask.title} · ${formatShortDate(nextDeadlineTask.dueDate)}` : 'Пока без сроков' }}</strong>
          </div>
          <div class="metric-pill soft">
            <span class="metric-label">Прогресс команды</span>
            <strong>{{ completionRate }}%</strong>
          </div>
        </div>

      </div>
    </section>

    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </div>

    <section v-if="activeTab === 'tasks'" class="tasks-shell">
      <div class="tasks-main">
        <div class="task-toolbar card">
          <div class="toolbar-main">
            <div>
              <div class="card-title">Рабочая доска</div>
              <div class="section-sub">Поиск, быстрые фильтры и актуальная картина по задачам команды.</div>
            </div>
            <div class="toolbar-controls">
              <div class="toolbar-search">
                <input v-model.trim="taskSearch" class="input" type="text" placeholder="Поиск по задаче или описанию" />
              </div>
              <button class="btn btn-primary mobile-plus-btn" @click="openTaskCreateModal">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
                Добавить задачу
              </button>
            </div>
          </div>

          <div class="smart-filters">
            <button class="filter-chip" :class="{ active: taskFilter === 'all' }" @click="taskFilter = 'all'">Все</button>
            <button class="filter-chip" :class="{ active: taskFilter === 'my' }" @click="taskFilter = 'my'">Мои</button>
            <button class="filter-chip" :class="{ active: taskFilter === 'overdue' }" @click="taskFilter = 'overdue'">Просрочено</button>
            <button class="filter-chip" :class="{ active: taskFilter === 'done' }" @click="taskFilter = 'done'">Готово</button>
          </div>

          <div class="task-kpis">
            <div class="kpi-box">
              <strong>{{ todoCount }}</strong>
              <span>к выполнению</span>
            </div>
            <div class="kpi-box">
              <strong>{{ inProgressCount }}</strong>
              <span>в работе</span>
            </div>
            <div class="kpi-box success">
              <strong>{{ doneTasks }}</strong>
              <span>готово</span>
            </div>
          </div>
        </div>

        <div class="tasks-workbench">
          <div class="kanban-board">
            <article v-for="lane in visibleTaskLanes" :key="lane.key" class="task-lane">
              <header class="lane-head">
                <div>
                  <h3>{{ lane.label }}</h3>
                  <p>{{ lane.help }}</p>
                </div>
                <span class="lane-count">{{ tasksByStatus[lane.key]?.length || 0 }}</span>
              </header>

              <div class="lane-body">
                <div v-if="!(tasksByStatus[lane.key]?.length)" class="lane-empty">
                  Ничего не найдено по текущему фильтру.
                </div>

                <button
                  v-for="task in tasksByStatus[lane.key]"
                  :key="task.id"
                  class="task-tile"
                  :class="{
                    selected: selectedTaskId === task.id,
                    overdue: isTaskOverdue(task),
                    done: task.status === 'done',
                  }"
                  @click="selectTask(task)"
                >
                  <div class="tile-top">
                    <button class="check-pill" :class="{ active: task.status === 'done' }" @click.stop="toggleTaskDone(task)">
                      {{ task.status === 'done' ? 'Выполнено' : 'Отметить готовой' }}
                    </button>
                    <span class="tile-deadline" :class="taskDeadlineClass(task)">{{ taskDeadlineLabel(task) }}</span>
                  </div>

                  <h4>{{ task.title }}</h4>
                  <p>{{ task.description || 'Без описания. Открой карточку и добавь детали.' }}</p>

                  <div class="tile-meta">
                    <div class="member-pill">
                      <span class="avatar-mini">{{ task.assignee?.initials || 'УЧ' }}</span>
                      <span>{{ task.assignee?.name || 'Без исполнителя' }}</span>
                    </div>
                    <div class="tile-side-metrics">
                      <span>{{ task.comments?.length || 0 }} комм.</span>
                      <span>{{ formatShortDate(task.updatedAt || task.created_at) }}</span>
                    </div>
                  </div>
                </button>
              </div>
            </article>
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
        <label class="btn btn-primary upload-btn mobile-plus-btn">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
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
          <button class="btn btn-ghost" @click="openPreview(file)">Просмотр</button>
          <button class="btn btn-ghost" @click="downloadFile(file)">Скачать</button>
          <button class="btn btn-ghost" @click="removeFile(file)">Удалить</button>
        </div>
      </div>
    </section>

    <section v-else-if="activeTab === 'chat'" class="chat-shell card">
      <div class="chat-topbar">
        <div>
          <div class="card-title">Командный чат</div>
          <div class="section-sub">Обсуждение проекта в реальном времени. История сообщений сохраняется в базе.</div>
        </div>
        <div class="chat-status-pack">
          <span class="connection-pill" :class="connectionState">{{ connectionLabel }}</span>
          <span class="presence-pill">Онлайн: {{ onlineConnections }}</span>
        </div>
      </div>

      <div ref="chatFeedRef" class="chat-thread">
        <div v-if="messagesLoading" class="state-card">Загружаем сообщения…</div>
        <div v-else-if="!messages.length" class="chat-empty">
          <div class="empty-illustration">💬</div>
          <strong>Чат проекта пока пуст</strong>
          <p>Напиши первое сообщение — все участники проекта увидят его сразу.</p>
        </div>

        <div
          v-for="message in messages"
          :key="message.id"
          class="message-row"
          :class="{ self: message.author_id === store.currentUser.id }"
        >
          <div v-if="message.author_id !== store.currentUser.id" class="message-avatar">{{ message.author?.initials || 'WS' }}</div>
          <div class="message-stack">
            <div class="message-meta">
              <strong>{{ message.author_id === store.currentUser.id ? 'Вы' : (message.author?.name || 'Участник') }}</strong>
              <span>{{ formatDateTime(message.created_at) }}</span>
            </div>
            <div class="message-bubble">
              <p>{{ message.body }}</p>
            </div>
          </div>
        </div>

        <div v-if="typingUsers.length" class="typing-bar">
          {{ typingUsers.join(', ') }} {{ typingUsers.length > 1 ? 'печатают…' : 'печатает…' }}
        </div>
      </div>

      <div class="chat-compose-modern">
        <textarea
          v-model.trim="messageDraft"
          class="composer-input"
          rows="3"
          placeholder="Напишите сообщение команде"
          @input="handleComposerInput"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <div class="compose-actions">
          <span class="section-sub">Enter — отправить, Shift+Enter — новая строка</span>
          <button class="btn btn-primary" @click="sendMessage">Отправить</button>
        </div>
      </div>
    </section>

    <FilePreviewModal v-if="previewFile" :file="previewFile" @close="previewFile = null" @download="handleFileDownload" />

    <ProjectAiSummaryTab
      v-else-if="activeTab === 'ai'"
      :project-id="projectId"
    />

    <section v-else-if="activeTab === 'members'" class="members-grid">
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
            <button class="btn btn-primary mobile-plus-btn" @click="addByEmail">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
              Добавить
            </button>
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

    <div v-if="isProjectEditModalOpen" class="modal-backdrop" @click.self="closeProjectEditModal">
      <section class="modal-window card" :style="heroStyle">
        <div class="detail-head">
          <div>
            <div class="detail-label">Параметры проекта</div>
            <h3>Редактирование проекта</h3>
          </div>
          <button class="btn btn-ghost" @click="closeProjectEditModal">Закрыть</button>
        </div>

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
          <button class="btn btn-danger-outline" @click="deleteProject">Удалить проект</button>
          <button class="btn btn-primary" @click="saveProject">Сохранить</button>
        </div>
      </section>
    </div>

    <div v-if="isTaskCreateModalOpen" class="modal-backdrop" @click.self="closeTaskCreateModal">
      <section class="modal-window card">
        <div class="detail-head">
          <div>
            <div class="detail-label">Новая задача</div>
            <h3>Добавить задачу</h3>
          </div>
          <button class="btn btn-ghost" @click="closeTaskCreateModal">Закрыть</button>
        </div>

        <div class="form-group">
          <label class="form-label">Название</label>
          <input v-model.trim="taskForm.title" class="input" type="text" placeholder="Например, сверстать главную страницу" />
        </div>
        <div class="form-group">
          <label class="form-label">Описание</label>
          <textarea v-model.trim="taskForm.description" class="textarea" rows="4" placeholder="Что именно нужно сделать и какой ожидается результат"></textarea>
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
        <div class="settings-actions">
          <button class="btn btn-ghost" @click="closeTaskCreateModal">Отмена</button>
          <button class="btn btn-primary mobile-plus-btn" @click="createTask">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            Создать задачу
          </button>
        </div>
      </section>
    </div>

    <div v-if="isTaskModalOpen && selectedTask" class="modal-backdrop" @click.self="closeTaskModal">
      <section class="modal-window task-modal card">
        <div class="detail-head">
          <div>
            <div class="detail-label">Карточка задачи</div>
            <h3>{{ selectedTask.title }}</h3>
          </div>
          <button class="btn btn-ghost" @click="closeTaskModal">Закрыть</button>
        </div>

        <div class="detail-badges">
          <span class="status-chip" :class="taskStatusTone(selectedTask.status)">{{ store.projectTaskStatusLabel(selectedTask.status) }}</span>
          <span class="meta-chip" v-if="selectedTask.completedAt">Закрыта {{ formatShortDate(selectedTask.completedAt) }}</span>
          <span class="meta-chip">Создал {{ selectedTask.creator?.name || 'Участник' }}</span>
        </div>

        <div class="detail-section">
          <label class="form-label">Описание</label>
          <textarea
            class="textarea"
            rows="5"
            :value="selectedTask.description"
            @change="changeTaskDescription(selectedTask, $event.target.value)"
            placeholder="Что нужно сделать, какие есть ограничения и критерии готовности"
          />
        </div>

        <div class="detail-grid">
          <label>
            <span>Статус</span>
            <select class="input" :value="selectedTask.status" @change="changeTaskStatus(selectedTask, $event.target.value)">
              <option value="todo">К выполнению</option>
              <option value="in_progress">В работе</option>
              <option value="done">Готово</option>
            </select>
          </label>
          <label>
            <span>Исполнитель</span>
            <select class="input" :value="selectedTask.assignee_id ? String(selectedTask.assignee_id) : ''" @change="changeTaskAssignee(selectedTask, $event.target.value)">
              <option value="">Без исполнителя</option>
              <option v-for="member in project.members || []" :key="member.id" :value="String(member.user_id)">
                {{ member.user.name }}
              </option>
            </select>
          </label>
          <label>
            <span>Срок</span>
            <input class="input" type="datetime-local" :value="toDateTimeLocal(selectedTask.due_date)" @change="changeTaskDueDate(selectedTask, $event.target.value)" />
          </label>
        </div>

        <div class="detail-actions">
          <button class="btn btn-ghost" @click="setTaskInProgress(selectedTask)">Перевести в работу</button>
          <button class="btn btn-primary" @click="toggleTaskDone(selectedTask)">
            {{ selectedTask.status === 'done' ? 'Вернуть в работу' : 'Отметить выполненной' }}
          </button>
          <button class="btn btn-danger-outline" @click="removeTask(selectedTask)">Удалить задачу</button>
        </div>

        <div class="detail-section">
          <div class="comment-head">
            <div>
              <div class="form-label">Комментарии</div>
              <div class="section-sub">Обсуждение по задаче и договорённости команды.</div>
            </div>
            <strong>{{ selectedTask.comments?.length || 0 }}</strong>
          </div>

          <div class="task-comments">
            <div v-if="!(selectedTask.comments?.length)" class="state-card compact">Пока нет комментариев. Добавь первый апдейт по задаче.</div>
            <div v-for="comment in selectedTask.comments" :key="comment.id" class="comment-card">
              <div class="comment-avatar">{{ comment.author?.initials || 'УЧ' }}</div>
              <div class="comment-body">
                <div class="comment-meta">
                  <strong>{{ comment.author?.name || 'Участник' }}</strong>
                  <span>{{ formatDateTime(comment.createdAt || comment.created_at) }}</span>
                </div>
                <p>{{ comment.body }}</p>
              </div>
            </div>
          </div>

          <div class="comment-compose">
            <textarea v-model.trim="commentDraft" class="textarea" rows="3" placeholder="Например: обновил экран, осталось подключить интеграцию" />
            <button class="btn btn-primary mobile-plus-btn" @click="submitComment">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
              Добавить комментарий
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { api } from '@/api/index.js'
import ProjectAiSummaryTab from '@/components/project/ProjectAiSummaryTab.vue'
import FilePreviewModal from '@/components/modals/FilePreviewModal.vue'
import { formatCountRu } from '@/utils/pluralize'

const route = useRoute()
const router = useRouter()
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
const taskSearch = ref('')
const taskFilter = ref('all')
const selectedTaskId = ref(null)
const commentDraft = ref('')
const isTaskModalOpen = ref(false)
const isTaskCreateModalOpen = ref(false)
const isProjectEditModalOpen = ref(false)
const previewFile = ref(null)
const connectionState = ref('offline')
const onlineConnections = ref(0)
const typingUsers = ref([])
const chatFeedRef = ref(null)
const chatSocket = ref(null)
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
  { key: 'ai', label: 'AI-сводка' },
  { key: 'members', label: 'Участники' },
]
const taskLanes = [
  { key: 'todo', label: 'К выполнению', help: 'Новые задачи и ближайшие планы' },
  { key: 'in_progress', label: 'В работе', help: 'То, над чем команда работает сейчас' },
  { key: 'done', label: 'Готово', help: 'Завершённые задачи и результаты' },
]

const typingTimers = new Map()
const typingNames = new Map()
let reconnectTimer = null
let typingDebounceTimer = null
let localTypingActive = false
let manualChatClose = false

const projectId = computed(() => Number(route.params.id))
const project = computed(() => store.projects.find((item) => item.id === projectId.value))
const isOwner = computed(() => {
  const membership = (project.value?.members || []).find((member) => member.user_id === store.currentUser.id)
  return membership?.role === 'owner'
})
const openTasks = computed(() => (project.value?.tasks || []).filter((task) => task.status !== 'done').length)
const doneTasks = computed(() => (project.value?.tasks || []).filter((task) => task.status === 'done').length)
const completionRate = computed(() => {
  const total = project.value?.tasks?.length || 0
  if (!total) return 0
  return Math.round((doneTasks.value / total) * 100)
})
const nextDeadlineTask = computed(() => {
  return [...(project.value?.tasks || [])]
    .filter((task) => task.status !== 'done' && task.dueDate)
    .sort((a, b) => a.dueDate - b.dueDate)[0] || null
})
const heroStyle = computed(() => ({ '--project-color': project.value?.color || '#7c3aed' }))
const todoCount = computed(() => (project.value?.tasks || []).filter((task) => task.status === 'todo').length)
const inProgressCount = computed(() => (project.value?.tasks || []).filter((task) => task.status === 'in_progress').length)
const selectedTask = computed(() => (project.value?.tasks || []).find((task) => task.id === selectedTaskId.value) || null)
const visibleTaskLanes = computed(() => taskLanes)
const filteredTasks = computed(() => {
  const search = taskSearch.value.trim().toLowerCase()
  return (project.value?.tasks || []).filter((task) => {
    const matchesSearch = !search || `${task.title} ${task.description}`.toLowerCase().includes(search)
    if (!matchesSearch) return false

    if (taskFilter.value === 'my') return task.assignee_id === store.currentUser.id
    if (taskFilter.value === 'overdue') return isTaskOverdue(task)
    if (taskFilter.value === 'done') return task.status === 'done'
    return true
  })
})
const tasksByStatus = computed(() => {
  return taskLanes.reduce((acc, lane) => {
    acc[lane.key] = filteredTasks.value.filter((task) => task.status === lane.key)
    return acc
  }, {})
})
const connectionLabel = computed(() => ({
  online: 'Подключено',
  connecting: 'Подключение…',
  offline: 'Офлайн',
}[connectionState.value] || 'Офлайн'))

watch(project, (value) => {
  if (!value) return
  projectForm.value = {
    name: value.name,
    description: value.description,
    color: value.color,
  }
  if (!value.tasks?.some((task) => task.id === selectedTaskId.value)) {
    selectedTaskId.value = null
    isTaskModalOpen.value = false
  }
}, { immediate: true })

watch(() => route.params.id, loadProject, { immediate: true })
watch(activeTab, async (tab) => {
  if (tab !== 'tasks') {
    isTaskModalOpen.value = false
    isTaskCreateModalOpen.value = false
  }
  if (tab === 'chat' && project.value) {
    await loadMessages()
    connectChat()
    return
  }
  disconnectChat()
})
watch(() => messages.value.length, scrollChatToBottom)

onBeforeUnmount(() => {
  disconnectChat()
})

async function loadProject() {
  loading.value = true
  loadError.value = false
  disconnectChat()
  try {
    messages.value = []
    typingUsers.value = []
    await store.fetchProject(projectId.value)
    selectedTaskId.value = null
    isTaskModalOpen.value = false
    isTaskCreateModalOpen.value = false
    isProjectEditModalOpen.value = false
    if (activeTab.value === 'chat') {
      await loadMessages()
      connectChat()
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function saveProject() {
  await store.updateProject(projectId.value, { ...projectForm.value })
  isProjectEditModalOpen.value = false
}

function resetProjectForm() {
  if (!project.value) return
  projectForm.value = {
    name: project.value.name,
    description: project.value.description,
    color: project.value.color,
  }
}

async function deleteProject() {
  if (!isOwner.value || !project.value) return
  if (!confirm(`Удалить проект «${project.value.name}»? Это действие необратимо.`)) return
  await store.deleteProject(projectId.value)
  isProjectEditModalOpen.value = false
  await router.push({ name: 'dashboard' })
}

async function createTask() {
  if (!taskForm.value.title) return
  const created = await store.createProjectTask(projectId.value, {
    title: taskForm.value.title,
    description: taskForm.value.description,
    due_date: taskForm.value.due_date || null,
    assignee_id: taskForm.value.assignee_id ? Number(taskForm.value.assignee_id) : null,
    status: 'todo',
  })
  taskForm.value = { title: '', description: '', due_date: '', assignee_id: '' }
  selectedTaskId.value = created?.id ?? selectedTaskId.value
  isTaskCreateModalOpen.value = false
  if (created?.id) {
    isTaskModalOpen.value = true
  }
}

function selectTask(task) {
  selectedTaskId.value = task.id
  isTaskModalOpen.value = true
}

async function changeTaskStatus(task, status) {
  await store.updateProjectTask(projectId.value, task.id, { status })
}

async function changeTaskDescription(task, description) {
  await store.updateProjectTask(projectId.value, task.id, { description })
}

async function changeTaskAssignee(task, assigneeId) {
  await store.updateProjectTask(projectId.value, task.id, { assignee_id: assigneeId ? Number(assigneeId) : null })
}

async function changeTaskDueDate(task, dueDate) {
  await store.updateProjectTask(projectId.value, task.id, { due_date: dueDate || null })
}

async function toggleTaskDone(task) {
  const nextStatus = task.status === 'done' ? 'todo' : 'done'
  await changeTaskStatus(task, nextStatus)
}

async function setTaskInProgress(task) {
  await changeTaskStatus(task, 'in_progress')
}

async function submitComment() {
  if (!selectedTask.value || !commentDraft.value) return
  await store.addProjectTaskComment(projectId.value, selectedTask.value.id, commentDraft.value)
  commentDraft.value = ''
}

async function removeTask(task) {
  if (!confirm(`Удалить задачу «${task.title}»?`)) return
  await store.deleteProjectTask(projectId.value, task.id)
  if (selectedTaskId.value === task.id) {
    selectedTaskId.value = null
    isTaskModalOpen.value = false
    commentDraft.value = ''
  }
}

function openProjectEditModal() {
  if (!isOwner.value) return
  resetProjectForm()
  isProjectEditModalOpen.value = true
}

function closeProjectEditModal() {
  isProjectEditModalOpen.value = false
}

function openTaskCreateModal() {
  taskForm.value = { title: '', description: '', due_date: '', assignee_id: '' }
  isTaskCreateModalOpen.value = true
}

function closeTaskCreateModal() {
  isTaskCreateModalOpen.value = false
}

function closeTaskModal() {
  isTaskModalOpen.value = false
  commentDraft.value = ''
}

async function uploadSharedFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  await store.uploadProjectFile(projectId.value, file)
  event.target.value = ''
}

function openPreview(file) {
  const short = file.name?.split('.').pop()?.toUpperCase() || 'FILE'
  previewFile.value = {
    id: file.id, name: file.name, size: store.humanSize(file.size_bytes),
    icon: file.icon, iconBg: file.icon_bg, type: short,
    mimeType: file.mime_type,
    entityType: 'projectFile', projectId: projectId.value
  }
}

async function downloadFile(file) {
  await api.downloadProjectFile(projectId.value, file.id, file.name)
}

async function handleFileDownload() {
  try {
    await api.downloadProjectFile(previewFile.value.projectId, previewFile.value.id, previewFile.value.name)
  } catch (e) {
    store.showToast('Ошибка скачивания: ' + e.message)
  }
}

async function removeFile(file) {
  if (!confirm(`Удалить файл «${file.name}»?`)) return
  await store.deleteProjectFile(projectId.value, file.id)
}

async function loadMessages() {
  messagesLoading.value = true
  try {
    messages.value = await store.fetchProjectMessages(projectId.value)
    scrollChatToBottom()
  } finally {
    messagesLoading.value = false
  }
}

function connectChat() {
  if (chatSocket.value && [WebSocket.OPEN, WebSocket.CONNECTING].includes(chatSocket.value.readyState)) return
  manualChatClose = false
  connectionState.value = 'connecting'

  const socket = new WebSocket(api.projectChatSocketUrl(projectId.value))
  chatSocket.value = socket

  socket.onopen = () => {
    connectionState.value = 'online'
  }

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data)

    if (payload.type === 'connection.ready' || payload.type === 'presence.update') {
      onlineConnections.value = payload.connections || 0
      return
    }

    if (payload.type === 'typing') {
      updateTypingState(payload)
      return
    }

    if (payload.type === 'message.created' && payload.message) {
      appendMessage(payload.message)
      return
    }

    if (payload.type === 'error' && payload.detail) {
      store.showToast(payload.detail)
    }
  }

  socket.onclose = () => {
    chatSocket.value = null
    connectionState.value = 'offline'
    onlineConnections.value = 0
    typingUsers.value = []
    if (!manualChatClose && activeTab.value === 'chat') {
      clearTimeout(reconnectTimer)
      reconnectTimer = setTimeout(() => connectChat(), 1800)
    }
  }

  socket.onerror = () => {
    connectionState.value = 'offline'
  }
}

function disconnectChat() {
  clearTimeout(reconnectTimer)
  clearTimeout(typingDebounceTimer)
  manualChatClose = true
  clearTypingIndicators()
  setTyping(false)
  if (chatSocket.value) {
    chatSocket.value.close()
    chatSocket.value = null
  }
  connectionState.value = 'offline'
  onlineConnections.value = 0
}

function appendMessage(message) {
  if (messages.value.some((item) => item.id === message.id)) return
  messages.value = [...messages.value, message].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  scrollChatToBottom()
}

async function sendMessage() {
  const body = messageDraft.value.trim()
  if (!body) return

  messageDraft.value = ''
  setTyping(false)

  const socket = chatSocket.value
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'message', body }))
    return
  }

  const created = await store.postProjectMessage(projectId.value, body)
  appendMessage(created)
}

function handleComposerInput() {
  if (!messageDraft.value.trim()) {
    setTyping(false)
    return
  }

  setTyping(true)
  clearTimeout(typingDebounceTimer)
  typingDebounceTimer = setTimeout(() => setTyping(false), 1200)
}

function setTyping(isTyping) {
  if (localTypingActive === isTyping) return
  localTypingActive = isTyping
  const socket = chatSocket.value
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'typing', is_typing: isTyping }))
  }
}

function updateTypingState(payload) {
  if (!payload.user_id || payload.user_id === store.currentUser.id) return

  if (!payload.is_typing) {
    clearTypingIndicators(payload.user_id)
    return
  }

  clearTypingIndicators(payload.user_id)
  typingNames.set(payload.user_id, payload.user_name)
  typingTimers.set(payload.user_id, setTimeout(() => clearTypingIndicators(payload.user_id), 1600))
  typingUsers.value = [...typingNames.values()]
}

function clearTypingIndicators(userId = null) {
  if (userId == null) {
    typingTimers.forEach((timer) => clearTimeout(timer))
    typingTimers.clear()
    typingNames.clear()
    typingUsers.value = []
    return
  }

  const timer = typingTimers.get(userId)
  if (timer) clearTimeout(timer)
  typingTimers.delete(userId)
  typingNames.delete(userId)
  typingUsers.value = [...typingNames.values()]
}

function scrollChatToBottom() {
  nextTick(() => {
    if (!chatFeedRef.value) return
    chatFeedRef.value.scrollTop = chatFeedRef.value.scrollHeight
  })
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

function isTaskOverdue(task) {
  if (!task?.dueDate || task.status === 'done') return false
  return task.dueDate.getTime() < Date.now()
}

function taskDeadlineLabel(task) {
  if (!task?.dueDate) return 'Без срока'
  if (task.status === 'done') return 'Закрыта'

  const oneDay = 1000 * 60 * 60 * 24
  const diffDays = Math.floor((task.dueDate.getTime() - Date.now()) / oneDay)
  if (diffDays < 0) return `Просрочено ${Math.abs(diffDays)} д.`
  if (diffDays === 0) return 'Сегодня'
  if (diffDays === 1) return 'Завтра'
  return `${diffDays} дн.`
}

function taskDeadlineClass(task) {
  if (task.status === 'done') return 'neutral'
  if (isTaskOverdue(task)) return 'danger'
  if (task?.dueDate && task.dueDate.getTime() - Date.now() < 1000 * 60 * 60 * 24 * 2) return 'warn'
  return 'normal'
}

function taskStatusTone(status) {
  return {
    todo: 'todo',
    in_progress: 'progress',
    done: 'done',
  }[status] || 'todo'
}

function formatDateTime(value) {
  if (!value) return 'Без даты'
  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatShortDate(value) {
  if (!value) return 'Без срока'
  return new Date(value).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'short',
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
.state-card.compact { padding: 16px; font-size: 14px; }
.state-card.error { color: var(--danger); }
.project-page { display: grid; gap: 18px; }
.project-hero {
  display: block;
}
.hero-copy {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--project-color) 16%, var(--surface)) 0%,
    var(--surface) 62%,
    color-mix(in srgb, var(--project-color) 10%, var(--surface)) 100%
  );
  border: 1px solid var(--border);
  border-radius: 28px;
  padding: 28px;
  position: relative;
}
.hero-badge {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface) 90%, transparent);
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
.hero-stats,
.hero-inline-metrics,
.task-kpis,
.detail-grid,
.row-2 {
  display: grid;
  gap: 12px;
}
.hero-stats {
  grid-template-columns: repeat(3, 1fr);
  margin-top: 22px;
}
.hero-stats strong { display: block; font-size: 18px; font-weight: 600; line-height: 1.25; }
.hero-stats span,
.metric-label,
.section-sub { color: var(--text-muted); font-size: 12px; }
.hero-inline-metrics {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 14px;
}
.metric-pill {
  padding: 14px 16px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface) 92%, transparent);
  border: 1px solid var(--border-soft);
  display: grid;
  gap: 4px;
}
.metric-pill.soft { background: color-mix(in srgb, var(--project-color) 12%, var(--surface)); }
.hero-edit-btn {
  position: absolute;
  top: 18px;
  right: 18px;
  padding: 7px 12px;
  font-size: 12px;
  border-radius: 10px;
}
.card-title { font-weight: 700; }
.input,
.textarea,
select.input,
.composer-input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 14px;
  font: inherit;
  background: var(--surface);
}
.input:focus,
.textarea:focus,
select.input:focus,
.composer-input:focus {
  outline: none;
  border-color: var(--accent-mid);
  box-shadow: 0 0 0 3px rgba(61, 82, 213, 0.08);
}
.textarea,
.composer-input { resize: vertical; }
.form-group { display: grid; gap: 8px; }
.form-label { font-size: 12px; color: var(--text-muted); }
.color-row { display: flex; gap: 10px; flex-wrap: wrap; }
.color-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
}
.color-btn.active { border-color: var(--text-primary); transform: scale(1.08); }
.settings-actions,
.detail-actions,
.compose-actions,
.file-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.btn-danger-outline {
  border: 1px solid color-mix(in srgb, var(--danger) 45%, white);
  color: var(--danger);
  background: var(--surface);
}
.btn-danger-outline:hover {
  background: color-mix(in srgb, var(--danger) 10%, white);
}
.tabs {
  display: flex;
  gap: 3px;
  background: var(--surface-2);
  border-radius: 16px;
  padding: 4px;
}
.tab {
  flex: 1;
  border: none;
  background: transparent;
  border-radius: 12px;
  padding: 11px 14px;
  cursor: pointer;
  font: inherit;
  color: var(--text-muted);
}
.tab.active {
  background: var(--surface);
  color: var(--text-primary);
  box-shadow: 0 6px 18px rgba(26,23,20,0.08);
}
.tasks-shell {
  display: block;
}
.wide-btn { width: 100%; justify-content: center; }
.tasks-main { display: grid; gap: 16px; }
.task-toolbar,
.task-detail,
.chat-shell {
  border-radius: 24px;
}
.toolbar-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 520px);
  gap: 14px;
  align-items: center;
}
.toolbar-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}
.smart-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}
.filter-chip {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 8px 12px;
  font: inherit;
  cursor: pointer;
}
.filter-chip.active {
  background: var(--accent-light);
  border-color: transparent;
  color: var(--accent);
}
.task-kpis {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 14px;
}
.kpi-box {
  background: var(--surface-2);
  border-radius: 18px;
  padding: 12px 14px;
}
.kpi-box.success {
  background: color-mix(in srgb, var(--success) 16%, var(--surface));
}
.kpi-box strong { display: block; font-size: 24px; }
.kpi-box span { color: var(--text-muted); font-size: 12px; }
.tasks-workbench {
  display: block;
}
.kanban-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.task-lane {
  background: var(--surface-2);
  border: 1px solid var(--border-soft);
  border-radius: 22px;
  padding: 14px;
  display: grid;
  gap: 12px;
  min-height: 520px;
}
.lane-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}
.lane-head h3 { font-size: 16px; margin-bottom: 4px; }
.lane-head p { color: var(--text-muted); font-size: 12px; }
.lane-count {
  min-width: 32px;
  height: 32px;
  border-radius: 12px;
  background: var(--surface);
  display: grid;
  place-items: center;
  font-weight: 700;
}
.lane-body {
  display: grid;
  gap: 12px;
  align-content: start;
}
.lane-empty {
  padding: 18px 14px;
  border: 1px dashed var(--border);
  border-radius: 18px;
  color: var(--text-muted);
  text-align: center;
  font-size: 13px;
}
.task-tile {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  background: var(--surface);
  border-radius: 20px;
  padding: 16px;
  display: grid;
  gap: 12px;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(26,23,20,0.06);
}
.task-tile.selected {
  border-color: var(--project-color);
  box-shadow: 0 16px 32px rgba(124,58,237,0.16);
}
.task-tile.overdue { border-color: rgba(220,38,38,0.24); }
.task-tile.done { opacity: 0.86; }
.tile-top,
.tile-meta,
.comment-head,
.detail-head,
.chat-topbar,
.chat-status-pack {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}
.check-pill,
.tile-deadline,
.status-chip,
.meta-chip,
.connection-pill,
.presence-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 12px;
  font-weight: 600;
}
.check-pill {
  border: 1px solid var(--border);
  background: var(--surface-2);
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.3;
  white-space: normal;
}
.check-pill.active {
  background: color-mix(in srgb, #16a34a 14%, white);
  color: #15803d;
  border-color: transparent;
}
.tile-deadline.normal,
.meta-chip,
.presence-pill {
  background: var(--surface-2);
  color: var(--text-secondary);
}
.tile-deadline.warn { background: color-mix(in srgb, #f59e0b 18%, white); color: #b45309; }
.tile-deadline.danger { background: color-mix(in srgb, #ef4444 14%, white); color: #b91c1c; }
.tile-deadline.neutral { background: color-mix(in srgb, #16a34a 14%, white); color: #15803d; }
.task-tile h4 { font-size: 16px; line-height: 1.35; }
.task-tile p {
  color: var(--text-secondary);
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.member-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.avatar-mini,
.comment-avatar,
.message-avatar,
.member-avatar {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: var(--accent-light);
  color: var(--accent);
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
}
.tile-side-metrics {
  display: flex;
  gap: 10px;
  color: var(--text-muted);
  font-size: 11px;
}
.detail-label {
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 4px;
}
.detail-head h3 { font-size: 24px; }
.detail-badges,
.detail-section,
.task-comments,
.comment-compose {
  display: grid;
  gap: 12px;
}
.status-chip.todo { background: var(--surface-2); color: var(--text-secondary); }
.status-chip.progress { background: color-mix(in srgb, #3b82f6 14%, white); color: #2563eb; }
.status-chip.done { background: color-mix(in srgb, #16a34a 14%, white); color: #15803d; }
.detail-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.detail-grid label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}
.detail-actions {
  flex-wrap: wrap;
}
.detail-actions .btn {
  flex: 1 1 190px;
  justify-content: center;
  text-align: center;
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(18, 24, 38, 0.5);
  display: grid;
  place-items: center;
  padding: 18px;
  z-index: 60;
  animation: modal-fade-in 0.2s ease;
}
.modal-window {
  width: min(860px, 100%);
  max-height: calc(100vh - 36px);
  overflow: auto;
  border-radius: 24px;
  display: grid;
  gap: 14px;
  animation: modal-window-in 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  transform-origin: top center;
}
.task-modal {
  width: min(980px, 100%);
}

@keyframes modal-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes modal-window-in {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
.comment-card {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
}
.comment-body {
  background: var(--surface-2);
  border-radius: 18px;
  padding: 12px 14px;
}
.comment-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  margin-bottom: 6px;
}
.comment-meta span { color: var(--text-muted); }
.comment-body p,
.message-bubble p { white-space: pre-wrap; }
.files-card { display: grid; gap: 14px; }
.files-head { align-items: center; }
.file-row,
.member-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 14px 0;
  border-top: 1px solid var(--border-soft);
}
.file-row:first-of-type,
.member-row:first-of-type { border-top: 0; }
.file-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 20px;
}
.file-copy strong,
.member-copy strong { display: block; margin-bottom: 4px; }
.file-copy span,
.member-copy span { color: var(--text-muted); font-size: 12px; }
.chat-shell {
  display: grid;
  gap: 14px;
  min-height: 720px;
}
.chat-thread {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--surface) 94%, transparent),
    color-mix(in srgb, var(--surface-2) 94%, transparent)
  );
  border: 1px solid var(--border-soft);
  border-radius: 24px;
  padding: 18px;
  display: grid;
  gap: 14px;
  overflow: auto;
  min-height: 520px;
  max-height: 65vh;
}
.chat-empty {
  display: grid;
  place-items: center;
  gap: 6px;
  min-height: 340px;
  text-align: center;
  color: var(--text-secondary);
}
.empty-illustration {
  width: 72px;
  height: 72px;
  border-radius: 24px;
  background: var(--surface);
  display: grid;
  place-items: center;
  font-size: 30px;
}
.message-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.message-row.self { justify-content: flex-end; }
.message-row.self .message-stack { align-items: flex-end; }
.message-stack {
  max-width: min(78%, 720px);
  display: grid;
  gap: 6px;
}
.message-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 12px;
  color: var(--text-muted);
}
.message-bubble {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: 20px 20px 20px 8px;
  padding: 14px 16px;
  box-shadow: 0 10px 24px rgba(26,23,20,0.05);
}
.message-row.self .message-bubble {
  background: color-mix(in srgb, var(--project-color) 13%, white);
  border-color: transparent;
  border-radius: 20px 20px 8px 20px;
}
.chat-compose-modern {
  background: var(--surface-2);
  border-radius: 22px;
  padding: 14px;
  display: grid;
  gap: 10px;
}
.composer-input {
  background: var(--surface);
  min-height: 110px;
  border-radius: 18px;
}
.connection-pill.online { background: color-mix(in srgb, #16a34a 15%, white); color: #15803d; }
.connection-pill.connecting { background: color-mix(in srgb, #f59e0b 18%, white); color: #b45309; }
.connection-pill.offline { background: color-mix(in srgb, #ef4444 12%, white); color: #b91c1c; }
.typing-bar {
  justify-self: start;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 12px;
  border: 1px solid var(--border-soft);
}
.members-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 18px;
  align-items: start;
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

@media (max-width: 1320px) {
  .tasks-shell,
  .members-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1080px) {
  .kanban-board,
  .detail-grid,
  .hero-stats,
  .hero-inline-metrics,
  .task-kpis,
  .toolbar-main,
  .toolbar-controls {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .tabs,
  .smart-filters,
  .compose-actions,
  .file-actions,
  .detail-actions,
  .settings-actions,
  .inline-row,
  .file-row,
  .member-row {
    grid-template-columns: 1fr;
    display: grid;
  }
  .message-stack { max-width: 100%; }
}

@media (max-width: 760px) {
  .project-page {
    gap: 14px;
  }

  .hero-copy {
    border-radius: 24px;
    padding: 22px;
  }

  .hero-copy h1 {
    font-size: 31px;
    line-height: 1.1;
  }

  .hero-copy p {
    font-size: 13px;
  }

  .hero-edit-btn {
    position: static;
    width: 100%;
    margin-bottom: 12px;
  }

  .hero-stats,
  .hero-inline-metrics,
  .task-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-stats div,
  .metric-pill,
  .kpi-box {
    border-radius: 16px;
  }

  .hero-stats strong {
    font-size: 17px;
  }

  .tabs {
    position: sticky;
    top: 0;
    z-index: 6;
    display: flex;
    flex-wrap: nowrap;
    gap: 6px;
    padding: 5px;
    border-radius: 20px;
    background: color-mix(in srgb, var(--surface) 82%, transparent);
    backdrop-filter: blur(16px);
    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    scroll-snap-type: x proximity;
  }

  .tabs::-webkit-scrollbar {
    display: none;
  }

  .tab {
    flex: 0 0 auto;
    min-height: 44px;
    min-width: max-content;
    padding: 8px 14px;
    border-radius: 15px;
    white-space: nowrap;
    scroll-snap-align: start;
  }

  .task-toolbar,
  .task-lane,
  .task-tile,
  .files-card,
  .chat-shell,
  .modal-window {
    border-radius: 22px;
  }

  .kanban-board {
    display: flex;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    padding-bottom: 4px;
  }

  .task-lane {
    min-width: min(86vw, 340px);
    min-height: 420px;
    scroll-snap-align: start;
  }

  .toolbar-controls,
  .row-2,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .mobile-plus-btn {
    justify-content: center;
    width: 100%;
  }

  .mobile-plus-btn svg {
    display: none;
  }

  .mobile-plus-btn::before {
    content: "+";
    font-size: 16px;
    font-weight: 700;
    line-height: 1;
  }

  .chat-shell {
    min-height: calc(100dvh - var(--header-h) - 132px);
  }

  .chat-thread {
    min-height: 360px;
    max-height: 52vh;
    border-radius: 18px;
  }

  .message-stack {
    max-width: min(88%, 420px);
  }

  .modal-backdrop {
    align-items: end;
    padding: 12px;
  }

  .modal-window {
    max-height: 86vh;
  }
}
</style>

