<template>
  <aside class="sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <div class="logo-mark">
        <svg viewBox="0 0 24 24"><path d="M12 3L2 8.5V15.5L12 21L22 15.5V8.5L12 3ZM12 5.15L20 9.5V15L12 18.85L4 15V9.5L12 5.15Z"/></svg>
      </div>
      <div>
        <div class="logo-text">WorkSpace</div>
        <div class="logo-sub">Student Platform</div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <div class="nav-section-label">Навигация</div>

      <RouterLink to="/" class="nav-item" active-class="active" exact>
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
        Главная
      </RouterLink>

      <div class="nav-item" @click="store.showToast('Расписание скоро!')">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg>
        Расписание
      </div>

      <!-- Courses Accordion -->
      <div class="nav-section-label" style="margin-top: 8px">Курсы</div>

      <div class="courses-header" @click="coursesOpen = !coursesOpen">
        <div class="courses-header-left">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;opacity:.7">
            <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
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

      <!-- Other links -->
      <div class="nav-section-label" style="margin-top: 8px">Другое</div>

      <div class="nav-item">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
        </svg>
        Уведомления
        <span class="notif-count">3</span>
      </div>

      <div class="nav-item">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
        </svg>
        Настройки
      </div>
    </nav>

    <!-- User profile -->
    <div class="sidebar-profile">
      <div class="avatar">{{ store.currentUser.initials }}</div>
      <div class="profile-info">
        <div class="profile-name">{{ store.currentUser.name }}</div>
        <div class="profile-role">{{ store.currentUser.role }}</div>
      </div>
      <button class="profile-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
const coursesOpen = ref(true)
const openAddCourse = inject('openAddCourse')
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

/* Logo */
.sidebar-logo {
  padding: 22px 20px 18px;
  border-bottom: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-mark {
  width: 32px; height: 32px;
  background: var(--accent);
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.logo-mark svg { width: 16px; height: 16px; fill: white; }
.logo-text { font-family: var(--font-display); font-size: 15px; font-weight: 600; letter-spacing: -0.2px; }
.logo-sub  { font-size: 10px; color: var(--text-muted); font-weight: 400; letter-spacing: 0.5px; text-transform: uppercase; }

/* Nav */
.sidebar-nav { flex: 1; overflow-y: auto; padding: 12px 0; }

.nav-section-label {
  font-size: 10px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase;
  color: var(--text-muted); padding: 8px 20px 4px;
}

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 16px; margin: 1px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer; font-size: 13.5px; font-weight: 400;
  color: var(--text-secondary);
  transition: background var(--transition), color var(--transition);
  user-select: none;
  text-decoration: none;
}
.nav-item:hover { background: var(--surface-2); color: var(--text-primary); }
.nav-item.active { background: var(--accent-light); color: var(--accent); font-weight: 500; }
.nav-item svg { width: 16px; height: 16px; flex-shrink: 0; opacity: 0.7; }
.nav-item.active svg { opacity: 1; }

.notif-count {
  margin-left: auto;
  font-size: 10px;
  background: var(--accent);
  color: white;
  border-radius: 99px;
  padding: 1px 6px;
  font-weight: 600;
}

/* Accordion */
.courses-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 16px; margin: 1px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer; font-size: 13.5px; font-weight: 500;
  color: var(--text-primary);
  transition: background var(--transition);
  user-select: none;
}
.courses-header:hover { background: var(--surface-2); }
.courses-header-left { display: flex; align-items: center; gap: 10px; }

.chevron { transition: transform var(--transition); width: 14px; height: 14px; color: var(--text-muted); }
.chevron.open { transform: rotate(90deg); }

.courses-list { overflow: hidden; transition: max-height 0.3s cubic-bezier(0.4,0,0.2,1); }
.courses-list.collapsed { max-height: 0; }
.courses-list.expanded  { max-height: 600px; }

.course-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 16px 7px 36px; margin: 1px 8px;
  border-radius: var(--radius-sm); cursor: pointer;
  font-size: 13px; color: var(--text-secondary);
  transition: background var(--transition), color var(--transition);
  user-select: none; text-decoration: none;
}
.course-item:hover { background: var(--surface-2); color: var(--text-primary); }
.course-item.active { color: var(--accent); background: var(--accent-light); font-weight: 500; }
.course-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.add-course-btn {
  display: flex; align-items: center; gap: 8px;
  margin: 6px 16px; padding: 8px 12px;
  border: 1.5px dashed var(--border); border-radius: var(--radius-sm);
  cursor: pointer; font-size: 12.5px; color: var(--text-muted);
  transition: all var(--transition); background: transparent;
  width: calc(100% - 32px); font-family: var(--font-body);
}
.add-course-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-light); }

/* Profile */
.sidebar-profile {
  padding: 14px 16px; border-top: 1px solid var(--border-soft);
  display: flex; align-items: center; gap: 10px;
}
.avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, #7b8ef5 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; color: white; flex-shrink: 0;
}
.profile-info { flex: 1; min-width: 0; }
.profile-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-role { font-size: 11px; color: var(--text-muted); }
.profile-btn {
  width: 28px; height: 28px; border-radius: 6px;
  border: 1px solid var(--border); background: transparent;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background var(--transition);
}
.profile-btn:hover { background: var(--surface-2); }
.profile-btn svg { width: 14px; height: 14px; color: var(--text-muted); }
</style>
