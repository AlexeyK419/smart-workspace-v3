<template>
  <nav class="mobile-tabbar" aria-label="Mobile navigation">
    <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="tab-link" :class="{ active: item.active }">
      <span class="tab-icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path v-for="path in item.paths" :key="path" :d="path" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span v-if="item.badge" class="tab-badge">{{ item.badge }}</span>
      </span>
      <span>{{ item.label }}</span>
    </RouterLink>

    <button class="tab-link" :class="{ active: coursesActive }" type="button" @click="openPicker('courses')">
      <span class="tab-icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 4 3 9l9 5 9-5-9-5Z" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M5 12v4l7 4 7-4v-4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
      <span>Курсы</span>
    </button>

    <button class="tab-link" :class="{ active: projectsActive }" type="button" @click="openPicker('projects')">
      <span class="tab-icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 6h16v10H4z" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M8 20h8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
      <span>Проекты</span>
    </button>
  </nav>

  <Transition name="sheet-fade">
    <div v-if="pickerOpen" class="picker-backdrop" @click.self="closePicker">
      <section class="picker-sheet">
        <header class="picker-head">
          <div>
            <div class="picker-kicker">{{ pickerMode === 'courses' ? 'Доступные курсы' : 'Доступные проекты' }}</div>
            <h3>{{ pickerMode === 'courses' ? 'Выберите курс' : 'Выберите проект' }}</h3>
          </div>
          <button class="picker-close" type="button" @click="closePicker">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12Z"/></svg>
          </button>
        </header>

        <div class="picker-list">
          <RouterLink
            v-for="item in pickerItems"
            :key="item.id"
            :to="item.to"
            class="picker-item"
            @click="closePicker"
          >
            <span class="picker-dot" :style="{ background: item.color }"></span>
            <span class="picker-copy">
              <strong>{{ item.name }}</strong>
              <span class="picker-meta">{{ item.meta }}</span>
            </span>
          </RouterLink>
          <div v-if="!pickerItems.length" class="picker-empty">
            {{ pickerMode === 'courses' ? 'Курсов пока нет.' : 'Проектов пока нет.' }}
          </div>
        </div>

        <div class="picker-actions">
          <button v-if="pickerMode === 'courses'" class="picker-action primary" type="button" @click="createCourse">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            Добавить курс
          </button>
          <button v-else-if="pickerMode === 'projects'" class="picker-action primary" type="button" @click="projectCreateOpen = true">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            Новый проект
          </button>
        </div>
      </section>
    </div>
  </Transition>

  <Transition name="sheet-fade">
    <div v-if="projectCreateOpen" class="picker-backdrop" @click.self="projectCreateOpen = false">
      <section class="picker-sheet picker-create">
        <header class="picker-head">
          <div>
            <div class="picker-kicker">Командная работа</div>
            <h3>Новый проект</h3>
          </div>
          <button class="picker-close" type="button" @click="projectCreateOpen = false">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12Z"/></svg>
          </button>
        </header>

        <form class="picker-form" @submit.prevent="submitProject">
          <div class="form-group">
            <label class="form-label">Название проекта *</label>
            <input v-model.trim="projectForm.name" class="form-input" type="text" placeholder="Например: Дипломный проект" required />
          </div>
          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea v-model.trim="projectForm.description" class="form-input" rows="3" placeholder="Коротко опишите цель и формат работы" />
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
          <div class="picker-actions">
            <button class="picker-action" type="button" @click="projectCreateOpen = false">Отмена</button>
            <button class="picker-action primary" type="submit" :disabled="creatingProject">
              {{ creatingProject ? 'Создаём...' : 'Создать проект' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </Transition>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { useChatsStore } from '@/stores/chats'
import { formatCountRu } from '@/utils/pluralize'

const route = useRoute()
const router = useRouter()
const store = useWorkspaceStore()
const chatsStore = useChatsStore()
const openAddCourse = inject('openAddCourse', null)
const pickerMode = ref('')
const pickerOpen = computed(() => !!pickerMode.value)
const projectCreateOpen = ref(false)
const creatingProject = ref(false)
const colorOptions = ['#7c3aed', '#3d52d5', '#2d7a4f', '#b45309', '#0891b2', '#dc2626']
const projectForm = ref({
  name: '',
  description: '',
  color: '#7c3aed',
})

const navItems = computed(() => [
  {
    to: '/',
    label: 'Главная',
    active: route.name === 'dashboard',
    paths: ['M3 10.5 12 3l9 7.5', 'M5 10v10h5v-6h4v6h5V10'],
  },
  {
    to: '/schedule',
    label: 'Расписание',
    active: route.name === 'schedule',
    paths: ['M7 3v4M17 3v4', 'M4 8h16', 'M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Z'],
  },
  {
    to: '/chats',
    label: 'Чаты',
    active: route.name === 'chats',
    badge: chatsStore.unreadTotal ? (chatsStore.unreadTotal > 9 ? '9+' : chatsStore.unreadTotal) : '',
    paths: ['M4 5h16v11H8l-4 4V5Z', 'M8 9h8M8 12h5'],
  },
])

const coursesActive = computed(() => route.name === 'course')
const projectsActive = computed(() => route.name === 'project')

const pickerItems = computed(() => {
  if (pickerMode.value === 'courses') {
    return store.courses.map((course) => ({
      id: course.id,
      to: `/course/${course.id}`,
      name: course.name,
      meta: course.teacher || course.semester || 'Курс',
      color: course.color,
    }))
  }

  if (pickerMode.value === 'projects') {
    return store.projects.map((project) => ({
      id: project.id,
      to: `/projects/${project.id}`,
      name: project.name,
      meta: formatCountRu(project.members?.length || 0, 'участник', 'участника', 'участников'),
      color: project.color,
    }))
  }

  return []
})

function openPicker(mode) {
  pickerMode.value = mode
}

function closePicker() {
  pickerMode.value = ''
  projectCreateOpen.value = false
}

function createCourse() {
  if (typeof openAddCourse === 'function') openAddCourse()
  closePicker()
}

async function submitProject() {
  if (!projectForm.value.name || creatingProject.value) return
  creatingProject.value = true
  try {
    const created = await store.createProject({ ...projectForm.value })
    projectForm.value = { name: '', description: '', color: '#7c3aed' }
    projectCreateOpen.value = false
    closePicker()
    if (created?.id) router.push(`/projects/${created.id}`)
  } finally {
    creatingProject.value = false
  }
}

watch(
  () => route.fullPath,
  () => closePicker()
)
</script>

<style scoped>
.mobile-tabbar {
  display: none;
}

@media (max-width: 760px) {
  .mobile-tabbar {
    position: fixed;
    left: max(12px, env(safe-area-inset-left));
    right: max(12px, env(safe-area-inset-right));
    bottom: max(10px, env(safe-area-inset-bottom));
    z-index: 45;
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 4px;
    min-height: 70px;
    padding: 8px;
    border: 1px solid color-mix(in srgb, var(--border) 72%, transparent);
    border-radius: 26px;
    background: color-mix(in srgb, var(--surface) 82%, transparent);
    box-shadow: 0 18px 50px rgba(10, 16, 28, 0.2);
    backdrop-filter: blur(20px);
  }

  .tab-link {
    position: relative;
    min-width: 0;
    display: grid;
    place-items: center;
    gap: 3px;
    padding: 7px 2px;
    border-radius: 18px;
    color: var(--text-muted);
    text-decoration: none;
    font-size: 11px;
    line-height: 1.1;
    transition: color var(--transition), background var(--transition), transform var(--transition);
  }

.tab-link.active {
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 14%, transparent);
    transform: translateY(-1px);
  }

  .tab-link {
    border: 0;
    background: transparent;
    cursor: pointer;
  }

  .tab-icon-wrap {
    position: relative;
    display: grid;
    place-items: center;
  }

  .tab-link svg {
    width: 22px;
    height: 22px;
  }

  .tab-badge {
    position: absolute;
    top: -6px;
    right: -9px;
    min-width: 17px;
    height: 17px;
    border-radius: 999px;
    padding: 0 5px;
    display: grid;
    place-items: center;
    background: var(--danger);
    color: #fff;
    font-size: 10px;
    font-weight: 800;
    line-height: 1;
  }

  .picker-backdrop {
    position: fixed;
    inset: 0;
    z-index: 55;
    background: rgba(12, 16, 24, 0.42);
    backdrop-filter: blur(6px);
    display: grid;
    align-items: end;
    padding: 12px;
  }

  .picker-sheet {
    background: color-mix(in srgb, var(--surface) 92%, transparent);
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    max-height: 70vh;
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
  }

  .picker-head {
    padding: 16px 16px 14px;
    border-bottom: 1px solid var(--border-soft);
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: start;
  }

  .picker-kicker {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 4px;
  }

  .picker-head h3 {
    font-family: var(--font-display);
    font-size: 20px;
    line-height: 1.15;
  }

  .picker-close {
    width: 36px;
    height: 36px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-secondary);
    display: grid;
    place-items: center;
    cursor: pointer;
  }

  .picker-close svg {
    width: 18px;
    height: 18px;
  }

  .picker-list {
    overflow: auto;
    padding: 10px;
    display: grid;
    gap: 8px;
  }

  .picker-actions {
    display: flex;
    gap: 8px;
    padding: 0 10px 12px;
    flex-wrap: wrap;
  }

  .picker-action {
    flex: 1 1 0;
    min-height: 42px;
    padding: 0 12px;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: color-mix(in srgb, var(--surface) 76%, transparent);
    color: var(--text-primary);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
  }

  .picker-action svg {
    width: 16px;
    height: 16px;
  }

  .picker-action.primary {
    background: color-mix(in srgb, var(--accent) 15%, transparent);
    color: var(--accent);
    border-color: color-mix(in srgb, var(--accent) 24%, transparent);
  }

  .picker-create {
    max-height: 82vh;
  }

  .picker-form {
    display: grid;
    gap: 12px;
    padding: 12px 16px 16px;
    overflow: auto;
  }

  .color-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .color-btn {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    border: 2px solid transparent;
    cursor: pointer;
  }

  .color-btn.active {
    border-color: var(--text-primary);
    transform: scale(1.08);
  }

  .picker-item {
    display: grid;
    grid-template-columns: 10px minmax(0, 1fr);
    gap: 10px;
    align-items: center;
    padding: 12px 12px;
    border-radius: 18px;
    text-decoration: none;
    color: var(--text-primary);
    background: color-mix(in srgb, var(--surface-2) 72%, transparent);
  }

  .picker-item:hover {
    background: color-mix(in srgb, var(--accent) 8%, var(--surface-2));
  }

  .picker-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .picker-copy {
    min-width: 0;
  }

  .picker-copy strong,
  .picker-copy .picker-meta {
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .picker-copy .picker-meta {
    color: var(--text-muted);
    font-size: 12.5px;
    line-height: 1.25;
    margin-top: 3px;
  }

  .picker-empty {
    padding: 16px;
    text-align: center;
    color: var(--text-muted);
  }

  .sheet-fade-enter-active,
  .sheet-fade-leave-active {
    transition: opacity 0.18s ease;
  }

  .sheet-fade-enter-from,
  .sheet-fade-leave-to {
    opacity: 0;
  }
}
</style>
