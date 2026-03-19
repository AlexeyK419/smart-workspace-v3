<template>
  <header class="header">
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

      <template v-else-if="route.name === 'projects'">
        <span class="breadcrumb-current">Командные проекты</span>
      </template>

      <template v-else-if="route.name === 'project' && currentProject">
        <RouterLink to="/projects" class="breadcrumb-item">Проекты</RouterLink>
        <span class="breadcrumb-sep">›</span>
        <span class="breadcrumb-current">{{ currentProject.name }}</span>
      </template>
    </div>

    <div class="header-right">
      <button class="header-btn" title="Поиск" @click="store.showToast('Поиск в разработке')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

const route = useRoute()
const router = useRouter()
const store = useWorkspaceStore()

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
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.breadcrumb-item {
  color: var(--text-muted);
  cursor: pointer;
  transition: color var(--transition);
  text-decoration: none;
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
</style>
