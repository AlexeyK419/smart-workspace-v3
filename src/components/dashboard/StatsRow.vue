<template>
  <div class="stats-row">
    <div class="stat-card" v-for="stat in stats" :key="stat.label">
      <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
      <div class="stat-label">{{ stat.label }}</div>
      <template v-if="stat.progress !== undefined">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: stat.progress + '%' }"></div>
        </div>
      </template>
      <div v-else class="stat-sub">{{ stat.sub }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()

const stats = computed(() => {
  const totalCourses = store.courses.length
  const openAssignments = store.allAssignments.filter((a) => a.status !== 'done').length
  const totalProjects = store.projects.length
  const avgProgress = store.courses.length
    ? Math.round(store.courses.reduce((acc, c) => acc + store.getCourseProgress(c), 0) / store.courses.length)
    : 0

  return [
    { value: totalCourses, label: 'Активных курса', color: 'var(--accent)', sub: 'Личное обучение' },
    { value: openAssignments, label: 'Личных дедлайнов', color: 'var(--warning)', sub: 'По вашим предметам' },
    { value: totalProjects, label: 'Командных проектов', color: '#7c3aed', sub: `${store.pendingProjectTasks.length} открытых задач` },
    { value: avgProgress + '%', label: 'Средний прогресс', color: 'var(--success)', progress: avgProgress },
  ]
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 11.5px;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.stat-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}

@media (max-width: 1150px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
