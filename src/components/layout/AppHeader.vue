<template>
  <header class="header">
    <div class="header-left">
      <button class="header-btn mobile-only" :aria-expanded="sidebarOpen" title="Меню" @click="$emit('toggle-sidebar')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 7h16M4 12h16M4 17h16"/>
        </svg>
      </button>

      <RouterLink to="/" class="mobile-brand" aria-label="WorkSpace">
        <span class="mobile-logo">W</span>
        <span>
          <strong>WorkSpace</strong>
          <small>Student Platform</small>
        </span>
      </RouterLink>

      <div class="breadcrumbs">
        <RouterLink to="/" class="breadcrumb-item">Главная</RouterLink>
        <span class="breadcrumb-sep">›</span>

        <template v-if="route.name === 'dashboard'">
          <span class="breadcrumb-current">Обзор</span>
        </template>

        <template v-else-if="route.name === 'course' && currentCourse">
          <span class="breadcrumb-item" @click="router.push('/')">Курсы</span>
          <span class="breadcrumb-sep">›</span>
          <span class="breadcrumb-current">{{ currentCourse.name }}</span>
        </template>

        <template v-else-if="route.name === 'schedule'">
          <span class="breadcrumb-current">Расписание</span>
        </template>

        <template v-else-if="route.name === 'chats'">
          <span class="breadcrumb-current">Чаты</span>
        </template>

        <template v-else-if="route.name === 'project' && currentProject">
          <span class="breadcrumb-item" @click="router.push('/')">Командные проекты</span>
          <span class="breadcrumb-sep">›</span>
          <span class="breadcrumb-current">{{ currentProject.name }}</span>
        </template>

        <template v-else-if="route.name === 'settings'">
          <span class="breadcrumb-current">Настройки</span>
        </template>
      </div>
    </div>

    <div class="header-right">
      <button class="header-btn theme-toggle" :title="themeTitle" @click="uiStore.toggleTheme()">
        <svg v-if="uiStore.theme === 'dark'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42ZM1 13h3v-2H1v2Zm10-12h2v3h-2V1Zm8.04 2.46-1.41-1.41-1.8 1.79 1.42 1.42 1.79-1.8ZM17.24 19.16l1.8 1.79 1.41-1.41-1.79-1.8-1.42 1.42ZM20 11v2h3v-2h-3ZM4.96 20.95l1.8-1.79-1.42-1.42-1.79 1.8 1.41 1.41ZM11 20h2v3h-2v-3Zm1-14a6 6 0 1 0 0 12 6 6 0 0 0 0-12Z"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="currentColor">
          <path d="M21.64 13A9 9 0 0 1 11 2.36 7 7 0 1 0 21.64 13Z"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { useUiStore } from '@/stores/ui'

defineProps({
  sidebarOpen: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()
const store = useWorkspaceStore()
const uiStore = useUiStore()
const themeTitle = computed(() => uiStore.theme === 'dark' ? 'Светлая тема' : 'Тёмная тема')

const currentCourse = computed(() =>
  store.courses.find((c) => String(c.id) === String(route.params.id))
)

const currentProject = computed(() =>
  store.projects.find((project) => String(project.id) === String(route.params.id))
)
</script>

<style scoped>
.header {
  height: var(--header-h);
  min-height: var(--header-h);
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  backdrop-filter: blur(14px);
}

.header-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  min-width: 0;
  overflow: hidden;
}

.breadcrumb-item {
  color: var(--text-muted);
  cursor: pointer;
  transition: color var(--transition);
  text-decoration: none;
  white-space: nowrap;
}

.breadcrumb-item:hover {
  color: var(--accent);
}

.breadcrumb-sep {
  color: var(--border);
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background var(--transition);
  position: relative;
}

.header-btn:hover {
  background: var(--surface-2);
}

.header-btn svg {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.mobile-only {
  display: none;
}

.mobile-brand {
  display: none;
}

@media (max-width: 980px) {
  .header {
    padding: 0 16px;
  }

  .mobile-only {
    display: inline-flex;
    flex-shrink: 0;
  }

  .breadcrumbs {
    gap: 4px;
    font-size: 12px;
  }

  .breadcrumb-sep,
  .breadcrumb-item:first-child {
    display: none;
  }
}

@media (max-width: 640px) {
  .header {
    gap: 10px;
    height: 78px;
    min-height: 78px;
    padding: 12px 14px 8px;
    border-bottom: 0;
    background:
      linear-gradient(180deg, color-mix(in srgb, var(--bg) 92%, transparent), color-mix(in srgb, var(--bg) 72%, transparent));
    backdrop-filter: blur(18px);
  }

  .breadcrumbs {
    display: none;
  }

  .mobile-brand {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text-primary);
    text-decoration: none;
  }

  .mobile-logo {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    color: #fff;
    background: linear-gradient(135deg, var(--accent), #8ea5ff);
    font-weight: 800;
    box-shadow: 0 10px 28px color-mix(in srgb, var(--accent) 24%, transparent);
  }

  .mobile-brand strong,
  .mobile-brand small {
    display: block;
    line-height: 1.1;
  }

  .mobile-brand strong {
    font-family: var(--font-display);
    font-size: 18px;
  }

  .mobile-brand small {
    margin-top: 3px;
    color: var(--text-muted);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .header-right {
    gap: 8px;
  }

  .header-btn {
    width: 40px;
    height: 40px;
    border-radius: 14px;
    background: color-mix(in srgb, var(--surface) 70%, transparent);
    box-shadow: 0 12px 30px rgba(10, 16, 28, 0.08);
  }

  .header-btn svg {
    width: 18px;
    height: 18px;
  }
}
</style>
