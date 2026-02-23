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
    </div>

    <div class="header-right">
      <button class="header-btn" title="Поиск" @click="store.showToast('Поиск в разработке')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
      </button>

      <button class="header-btn" title="Уведомления">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
        </svg>
        <div class="notif-dot"></div>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

const route  = useRoute()
const router = useRouter()
const store  = useWorkspaceStore()

const currentCourse = computed(() =>
  store.courses.find((c) => String(c.id) === String(route.params.id))
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

.breadcrumbs { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.breadcrumb-item { color: var(--text-muted); cursor: pointer; transition: color var(--transition); text-decoration: none; }
.breadcrumb-item:hover { color: var(--accent); }
.breadcrumb-sep { color: var(--border); }
.breadcrumb-current { color: var(--text-primary); font-weight: 500; }

.header-right { display: flex; align-items: center; gap: 10px; }

.header-btn {
  width: 34px; height: 34px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: transparent;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background var(--transition);
  position: relative;
}
.header-btn:hover { background: var(--surface-2); }
.header-btn svg { width: 16px; height: 16px; color: var(--text-secondary); }
.notif-dot {
  position: absolute; top: 7px; right: 7px;
  width: 6px; height: 6px;
  background: var(--accent); border-radius: 50%;
  border: 1.5px solid var(--surface);
}
</style>
