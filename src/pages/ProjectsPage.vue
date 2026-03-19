<template>
  <div class="projects-page">
    <div class="page-head">
      <div>
        <div class="page-title">Командные проекты</div>
        <div class="page-sub">Создавай рабочие пространства для групповых проектов, приглашай участников и распределяй задачи.</div>
      </div>
      <RouterLink v-if="store.projects.length" to="/projects" class="page-chip">{{ store.projects.length }} проектов</RouterLink>
    </div>

    <div class="projects-layout">
      <section class="card create-card">
        <div class="card-header">
          <div>
            <div class="card-title">Новый проект</div>
            <div class="create-sub">Общие задачи, файлы и командный чат в одном месте.</div>
          </div>
        </div>

        <form class="create-form" @submit.prevent="submitProject">
          <div class="form-group">
            <label class="form-label">Название проекта</label>
            <input v-model.trim="form.name" class="input" type="text" placeholder="Например, Курсовой проект по Вебу" required />
          </div>

          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea v-model.trim="form.description" class="textarea" rows="4" placeholder="Кратко опиши цель проекта и что нужно сделать"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">Цвет проекта</label>
            <div class="color-row">
              <button
                v-for="color in colorOptions"
                :key="color"
                type="button"
                class="color-btn"
                :class="{ active: form.color === color }"
                :style="{ background: color }"
                @click="form.color = color"
              />
            </div>
          </div>

          <button class="btn btn-primary create-btn" :disabled="creating">
            {{ creating ? 'Создаём…' : 'Создать проект' }}
          </button>
        </form>
      </section>

      <section class="projects-board">
        <div class="board-head">
          <div>
            <div class="board-title">Ваши проекты</div>
            <div class="board-sub">Каждый проект доступен только его участникам.</div>
          </div>
        </div>

        <div v-if="!store.projects.length" class="empty-card">
          <div class="empty-icon">👥</div>
          <div class="empty-title">Пока нет командных проектов</div>
          <p>Создай первый проект слева и пригласи участников по email или через поиск пользователей.</p>
        </div>

        <div v-else class="projects-grid">
          <RouterLink
            v-for="project in store.projects"
            :key="project.id"
            :to="`/projects/${project.id}`"
            class="project-card"
          >
            <div class="project-card-head">
              <div class="project-mark" :style="{ background: project.color }"></div>
              <div class="project-role">{{ memberRole(project) }}</div>
            </div>

            <h3>{{ project.name }}</h3>
            <p>{{ project.description || 'Без описания — открой проект и добавь детали.' }}</p>

            <div class="project-meta">
              <div>
                <strong>{{ project.members?.length || 0 }}</strong>
                <span>участников</span>
              </div>
              <div>
                <strong>{{ openTasks(project) }}</strong>
                <span>активных задач</span>
              </div>
              <div>
                <strong>{{ project.files?.length || 0 }}</strong>
                <span>общих файлов</span>
              </div>
            </div>

            <div class="members-strip">
              <div v-for="member in (project.members || []).slice(0, 4)" :key="member.id" class="member-avatar">
                {{ member.user.initials }}
              </div>
              <div v-if="(project.members || []).length > 4" class="member-avatar muted">
                +{{ project.members.length - 4 }}
              </div>
            </div>
          </RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

const router = useRouter()
const store = useWorkspaceStore()
const creating = ref(false)
const form = ref({
  name: '',
  description: '',
  color: '#7c3aed',
})

const colorOptions = ['#7c3aed', '#3d52d5', '#2d7a4f', '#b45309', '#0891b2', '#dc2626']

function memberRole(project) {
  const membership = (project.members || []).find((member) => member.user_id === store.currentUser.id)
  return membership?.role === 'owner' ? 'Владелец' : 'Участник'
}

function openTasks(project) {
  return (project.tasks || []).filter((task) => task.status !== 'done').length
}

async function submitProject() {
  creating.value = true
  try {
    const created = await store.createProject({ ...form.value })
    form.value = { name: '', description: '', color: '#7c3aed' }
    router.push(`/projects/${created.id}`)
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.projects-page { display: grid; gap: 20px; }
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 6px;
}
.page-sub {
  color: var(--text-muted);
  max-width: 760px;
}
.page-chip {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 12px;
}
.projects-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
}
.create-card { align-self: start; }
.create-sub {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 12px;
}
.create-form { display: grid; gap: 2px; }
.input,
.textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
  font: inherit;
  background: var(--surface);
}
.textarea { resize: vertical; }
.input:focus,
.textarea:focus {
  outline: none;
  border-color: var(--accent-mid);
  box-shadow: 0 0 0 3px rgba(61, 82, 213, 0.08);
}
.color-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.color-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
}
.color-btn.active {
  border-color: var(--text-primary);
  transform: scale(1.08);
}
.create-btn { width: 100%; justify-content: center; margin-top: 6px; }
.projects-board { display: grid; gap: 16px; }
.board-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.board-title {
  font-size: 18px;
  font-weight: 600;
}
.board-sub {
  color: var(--text-muted);
  font-size: 12px;
  margin-top: 4px;
}
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}
.project-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px;
  text-decoration: none;
  color: inherit;
  display: grid;
  gap: 14px;
  box-shadow: var(--shadow);
}
.project-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
.project-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.project-mark {
  width: 44px;
  height: 12px;
  border-radius: 999px;
}
.project-role {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.project-card h3 {
  font-size: 18px;
  font-weight: 600;
}
.project-card p {
  color: var(--text-secondary);
  min-height: 68px;
}
.project-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.project-meta strong {
  display: block;
  font-size: 18px;
}
.project-meta span {
  font-size: 11px;
  color: var(--text-muted);
}
.members-strip {
  display: flex;
  align-items: center;
  gap: 8px;
}
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
.member-avatar.muted {
  background: var(--surface-2);
  color: var(--text-muted);
}
.empty-card {
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: 20px;
  padding: 32px;
  text-align: center;
}
.empty-icon { font-size: 32px; margin-bottom: 10px; }
.empty-title { font-size: 18px; font-weight: 600; margin-bottom: 6px; }
.empty-card p { color: var(--text-muted); }

@media (max-width: 980px) {
  .projects-layout { grid-template-columns: 1fr; }
}
</style>
