<template>
  <section class="card overview-card">
    <div class="card-header">
      <div>
        <div class="card-title">Командные проекты</div>
        <div class="overview-sub">Общие задачи, материалы и обсуждения команды</div>
      </div>
      <RouterLink to="/projects" class="link-btn">Открыть</RouterLink>
    </div>

    <div v-if="!store.projects.length" class="empty-state">
      Пока нет проектов. Создай первый и пригласи участников по email.
    </div>

    <RouterLink
      v-for="project in previewProjects"
      :key="project.id"
      :to="`/projects/${project.id}`"
      class="project-row"
    >
      <div class="project-color" :style="{ background: project.color }"></div>
      <div class="project-copy">
        <strong>{{ project.name }}</strong>
        <span>{{ project.members?.length || 0 }} участников · {{ openTasks(project) }} активных задач</span>
      </div>
      <div class="project-arrow">→</div>
    </RouterLink>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
const previewProjects = computed(() => store.projects.slice(0, 3))

function openTasks(project) {
  return (project.tasks || []).filter((task) => task.status !== 'done').length
}
</script>

<style scoped>
.overview-card { display: grid; gap: 12px; }
.overview-sub {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}
.link-btn {
  text-decoration: none;
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
}
.project-row {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--border-soft);
  text-decoration: none;
  color: inherit;
}
.project-row:hover {
  background: var(--surface-2);
}
.project-color {
  width: 10px;
  height: 42px;
  border-radius: 999px;
}
.project-copy strong {
  display: block;
  margin-bottom: 4px;
}
.project-copy span {
  color: var(--text-muted);
  font-size: 12px;
}
.project-arrow {
  color: var(--text-muted);
  font-size: 18px;
}
.empty-state {
  padding: 14px;
  border-radius: 14px;
  background: var(--surface-2);
  color: var(--text-muted);
  font-size: 13px;
}
</style>
