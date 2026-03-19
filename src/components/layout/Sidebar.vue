<template>
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-mark">
        <svg viewBox="0 0 24 24"><path d="M12 3L2 8.5V15.5L12 21L22 15.5V8.5L12 3ZM12 5.15L20 9.5V15L12 18.85L4 15V9.5L12 5.15Z" fill="white"/></svg>
      </div>
      <div>
        <div class="logo-text">WorkSpace</div>
        <div class="logo-sub">Student Platform</div>
      </div>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section-label">Навигация</div>

      <RouterLink to="/" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
        Главная
      </RouterLink>

      <RouterLink to="/schedule" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm-8 4H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
        Расписание
      </RouterLink>

      <RouterLink to="/projects" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
        Проекты
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

      <div class="project-list">
        <RouterLink
          v-for="project in previewProjects"
          :key="project.id"
          :to="`/projects/${project.id}`"
          class="project-item"
          active-class="active"
        >
          <div class="project-dot" :style="{ background: project.color }"></div>
          <div class="project-copy">
            <span>{{ project.name }}</span>
            <small>{{ project.members?.length || 0 }} участников</small>
          </div>
        </RouterLink>

        <RouterLink to="/projects" class="project-more">Все проекты</RouterLink>
      </div>

      <div class="nav-section-label" style="margin-top: 8px">Другое</div>

      <div class="nav-item" @click="store.showToast('Настройки в разработке')">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22l-1.92 3.32c-.12.22-.07.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
        </svg>
        Настройки
      </div>
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
  </aside>
</template>

<script setup>
import { ref, inject, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'

const store = useWorkspaceStore()
const authStore = useAuthStore()
const router = useRouter()
const coursesOpen = ref(true)
const openAddCourse = inject('openAddCourse')

const previewProjects = computed(() => store.projects.slice(0, 4))

async function logout() {
  await authStore.logout()
  router.replace('/welcome')
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 10;
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
.project-item,
.project-more {
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
.project-item:hover,
.project-more:hover {
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
.project-copy small,
.project-more {
  color: var(--text-muted);
  font-size: 11px;
}
.project-list { display: grid; }
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
</style>
