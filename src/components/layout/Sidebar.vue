<template>
  <aside class="sidebar" :class="{ open }">
    <div class="sidebar-logo">
      <div class="logo-mark">
        <svg viewBox="0 0 24 24"><path d="M12 3L2 8.5V15.5L12 21L22 15.5V8.5L12 3ZM12 5.15L20 9.5V15L12 18.85L4 15V9.5L12 5.15Z" fill="white"/></svg>
      </div>
      <div>
        <div class="logo-text">WorkSpace</div>
        <div class="logo-sub">Student Platform</div>
      </div>
      <button class="sidebar-close" type="button" aria-label="Закрыть меню" @click="emitClose">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 6l12 12M18 6 6 18"/>
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section-label">Навигация</div>

      <RouterLink to="/" class="nav-item" active-class="active" @click="emitClose">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
        Главная
      </RouterLink>

      <RouterLink to="/schedule" class="nav-item" active-class="active" @click="emitClose">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm-8 4H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
        Расписание
      </RouterLink>

      <RouterLink to="/chats" class="nav-item" active-class="active" @click="emitClose">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16c1.1 0 2 .9 2 2v9c0 1.1-.9 2-2 2H8.83L4 21v-4H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2Zm0 2v9h2v1.7L8.17 15H20V6H4Zm4 3h8v2H8V9Zm0 3h5v2H8v-2Z"/></svg>
        <span class="nav-copy">Чаты</span>
        <span v-if="chatsStore.unreadTotal" class="nav-badge">{{ chatsStore.unreadTotal > 99 ? '99+' : chatsStore.unreadTotal }}</span>
      </RouterLink>

      <div class="nav-section-label" style="margin-top: 8px">Курсы</div>

      <div class="courses-header" @click="coursesOpen = !coursesOpen">
        <div class="courses-header-left">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;opacity:.7">
            <path d="M12 3 1 9l11 6 9-4.91V17h2V9L12 3Zm0 13L4.74 12 12 8.04 19.26 12 12 16Zm-7 1.5V14l7 3.82L19 14v3.5L12 21l-7-3.5Z"/>
          </svg>
          Мои курсы
        </div>
        <svg class="chevron" :class="{ open: coursesOpen }" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>

      <div class="courses-list" :class="coursesOpen ? 'expanded' : 'collapsed'">
        <RouterLink
          v-for="course in store.courses"
          :key="course.id"
          :to="`/course/${course.id}`"
          class="course-item"
          active-class="active"
          @click="emitClose"
        >
          <div class="course-dot" :style="{ background: course.color }"></div>
          {{ course.name }}
        </RouterLink>

        <button class="add-course-btn" @click.stop="openAddCourse()">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:13px;height:13px">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          Добавить курс
        </button>
      </div>

      <div class="nav-section-label" style="margin-top: 8px">Командная работа</div>

      <div class="courses-header" @click="projectsOpen = !projectsOpen">
        <div class="courses-header-left">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;opacity:.7">
            <path d="M4 5h16v10H4zM2 3v14h20V3H2Zm4 16h12v2H6z"/>
          </svg>
          Командные проекты
        </div>
        <svg class="chevron" :class="{ open: projectsOpen }" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </div>

      <div class="project-list" :class="projectsOpen ? 'expanded' : 'collapsed'">

        <RouterLink
          v-for="project in previewProjects"
          :key="project.id"
          :to="`/projects/${project.id}`"
          class="project-item"
          active-class="active"
          @click="emitClose"
        >
          <div class="project-dot" :style="{ background: project.color }"></div>
          <div class="project-copy">
            <span>{{ project.name }}</span>
            <small>{{ project.members?.length || 0 }} участников</small>
          </div>
        </RouterLink>

        <button class="add-course-btn" type="button" @click.stop="openProjectModal">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:13px;height:13px">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          Новый проект
        </button>
      </div>

      <div class="nav-section-label" style="margin-top: 8px">Другое</div>

      <RouterLink to="/settings" class="nav-item" active-class="active" @click="emitClose">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22l-1.92 3.32c-.12.22-.07.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
        </svg>
        Настройки
      </RouterLink>
    </nav>

    <div class="sidebar-profile">
      <div class="avatar">{{ store.currentUser.initials }}</div>
      <div class="profile-info">
        <div class="profile-name">{{ store.currentUser.name }}</div>
        <div class="profile-role">{{ store.currentUser.role }}</div>
      </div>
      <button class="logout-btn" @click="logout">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
          <polyline points="16 17 21 12 16 7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
      </button>
    </div>

    <div v-if="projectModalOpen" class="modal-overlay" @click.self="closeProjectModal">
      <div class="modal" style="max-width: 440px">
        <div class="modal-header">
          <div class="modal-title">Новый проект</div>
          <button class="modal-close" type="button" @click="closeProjectModal">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
        <form class="modal-body project-form" @submit.prevent="submitProject">
          <div class="form-group">
            <label class="form-label">Название проекта *</label>
            <input
              v-model.trim="projectForm.name"
              class="form-input"
              type="text"
              placeholder="Например: Дипломный проект"
              required
            />
          </div>
          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea
              v-model.trim="projectForm.description"
              class="form-input textarea-input"
              rows="3"
              placeholder="Коротко опишите цель и формат работы"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Цвет проекта</label>
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
        </form>
        <div class="modal-footer">
          <button class="btn btn-ghost" type="button" @click="closeProjectModal">Отмена</button>
          <button class="btn btn-primary" type="button" :disabled="creatingProject" @click="submitProject">
            {{ creatingProject ? 'Создаём...' : 'Создать проект' }}
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, inject, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'
import { useChatsStore } from '@/stores/chats'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

const store = useWorkspaceStore()
const authStore = useAuthStore()
const chatsStore = useChatsStore()
const router = useRouter()
const coursesOpen = ref(true)
const projectsOpen = ref(true)
const openAddCourse = inject('openAddCourse')
const projectModalOpen = ref(false)
const creatingProject = ref(false)
const projectForm = ref({
  name: '',
  description: '',
  color: '#7c3aed',
})

const colorOptions = ['#7c3aed', '#3d52d5', '#2d7a4f', '#b45309', '#0891b2', '#dc2626']
const previewProjects = computed(() => store.projects.slice(0, 4))

function emitClose() {
  emit('close')
}

function openProjectModal() {
  projectModalOpen.value = true
}

function closeProjectModal() {
  projectModalOpen.value = false
}

async function submitProject() {
  creatingProject.value = true
  try {
    const created = await store.createProject({ ...projectForm.value })
    projectForm.value = { name: '', description: '', color: '#7c3aed' }
    closeProjectModal()
    emitClose()
    router.push(`/projects/${created.id}`)
  } finally {
    creatingProject.value = false
  }
}

async function logout() {
  emitClose()
  await authStore.logout()
  router.replace('/welcome')
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--surface) 94%, transparent) 0%, color-mix(in srgb, var(--surface) 88%, transparent) 100%);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 10;
  backdrop-filter: blur(16px);
}

.sidebar-close {
  display: none;
  margin-left: auto;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  align-items: center;
  justify-content: center;
}

.sidebar-close svg {
  width: 16px;
  height: 16px;
}
.sidebar-logo {
  padding: 22px 20px 18px;
  border-bottom: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-mark {
  width: 32px;
  height: 32px;
  background: var(--accent);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.logo-mark svg {
  width: 16px;
  height: 16px;
  fill: white;
}
.logo-text {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.2px;
}
.logo-sub {
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 400;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}
.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 8px 20px 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  margin: 1px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 400;
  color: var(--text-secondary);
  transition: background var(--transition), color var(--transition);
  user-select: none;
  text-decoration: none;
}
.nav-item:hover {
  background: var(--surface-2);
  color: var(--text-primary);
}
.nav-item.active {
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 500;
}
.nav-item svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  opacity: 0.7;
}
.nav-item.active svg {
  opacity: 1;
}
.nav-copy {
  flex: 1;
}
.nav-badge {
  margin-left: auto;
  min-width: 22px;
  height: 20px;
  border-radius: 999px;
  padding: 0 7px;
  background: var(--danger);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}
.courses-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 16px;
  margin: 1px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text-primary);
  transition: background var(--transition);
  user-select: none;
}
.courses-header:hover { background: var(--surface-2); }
.courses-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.chevron {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  transition: transform var(--transition);
}
.chevron.open { transform: rotate(90deg); }
.courses-list {
  overflow: hidden;
  transition: max-height .2s ease;
}
.courses-list.expanded { max-height: 500px; }
.courses-list.collapsed { max-height: 0; }
.course-item,
.add-course-btn,
.project-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 4px 16px 4px 36px;
  padding: 8px 10px;
  border-radius: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.course-item:hover,
.add-course-btn:hover,
.project-item:hover {
  background: var(--surface-2);
}
.course-item.active,
.project-item.active {
  color: var(--accent);
  background: var(--accent-light);
}
.course-dot,
.project-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.project-copy {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.project-copy span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.project-copy small {
  color: var(--text-muted);
  font-size: 11px;
}
.project-list {
  display: grid;
  overflow: hidden;
  transition: max-height .2s ease;
}
.project-list.expanded { max-height: 520px; }
.project-list.collapsed { max-height: 0; }
.sidebar-profile {
  padding: 16px;
  border-top: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: var(--accent-light);
  color: var(--accent);
  display: grid;
  place-items: center;
  font-weight: 700;
  flex-shrink: 0;
}
.profile-info { min-width: 0; }
.profile-name {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.profile-role {
  font-size: 11px;
  color: var(--text-muted);
}
.logout-btn {
  margin-left: auto;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  display: grid;
  place-items: center;
}
.logout-btn:hover { background: var(--surface-2); }
.logout-btn svg {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}
.project-form {
  display: block;
}
.textarea-input {
  resize: vertical;
}
.color-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.color-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
}
.color-btn.active {
  border-color: var(--text-primary);
}

@media (max-width: 980px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    height: 100dvh;
    max-width: min(86vw, 320px);
    transform: translateX(-100%);
    transition: transform var(--transition);
    z-index: 30;
    box-shadow: none;
  }

  .sidebar.open {
    transform: translateX(0);
    box-shadow: var(--shadow-lg);
  }

  .sidebar-close {
    display: inline-flex;
  }

}
</style>
