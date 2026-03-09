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

      <RouterLink to="/" class="nav-item" active-class="active" exact>
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
        Главная
      </RouterLink>

      <RouterLink to="/schedule" class="nav-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm-8 4H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
        Расписание
      </RouterLink>

      <div class="nav-section-label" style="margin-top: 8px">Курсы</div>

      <div class="courses-header" @click="coursesOpen = !coursesOpen">
        <div class="courses-header-left">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;opacity:.7">
            <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
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
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'

const store = useWorkspaceStore()
const authStore = useAuthStore()
const router = useRouter()
const coursesOpen = ref(true)
const openAddCourse = inject('openAddCourse')

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
.courses-header:hover {
  background: var(--surface-2);
}
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
.chevron.open {
  transform: rotate(90deg);
}
.courses-list {
  overflow: hidden;
  transition: max-height .2s ease;
}
.courses-list.expanded {
  max-height: 500px;
}
.courses-list.collapsed {
  max-height: 0;
}
.course-item,
.add-course-btn {
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
.add-course-btn:hover {
  background: var(--surface-2);
}
.course-item.active {
  color: var(--accent);
  background: var(--accent-light);
}
.course-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex-shrink: 0;
}
.add-course-btn {
  width: calc(100% - 52px);
  border: 1px dashed var(--border);
}
.sidebar-profile {
  border-top: 1px solid var(--border-soft);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: var(--accent-light);
  color: var(--accent);
  display: grid;
  place-items: center;
  font-weight: 700;
}
.profile-info {
  min-width: 0;
  flex: 1;
}
.profile-name {
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.profile-role {
  color: var(--text-muted);
  font-size: 12px;
  margin-top: 2px;
}
.logout-btn {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: transparent;
  display: grid;
  place-items: center;
  cursor: pointer;
}
.logout-btn:hover {
  background: var(--surface-2);
}
.logout-btn svg {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}
</style>
