<template>
  <div class="card" style="align-self: start">
    <div class="card-header">
      <div class="card-title">Предстоящие задания</div>
      <select class="sort-select" v-model="sortBy">
        <option value="date">По дате</option>
        <option value="course">По курсу</option>
        <option value="status">По статусу</option>
      </select>
    </div>

    <div v-for="a in sorted" :key="a.id" class="assignment-item">
      <div class="assignment-color" :style="{ background: a.courseColor }"></div>
      <div class="assignment-body">
        <div class="assignment-title">{{ a.title }}</div>
        <div class="assignment-course">{{ a.course }}</div>
        <div class="assignment-meta">
          <span class="deadline-badge" :class="store.urgencyClass(a.deadline)">
            {{ a.deadline }}
          </span>
          <span class="chip" :class="'chip-' + a.status">
            {{ store.statusLabel(a.status) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const store  = useWorkspaceStore()
const sortBy = ref('date')

const sorted = computed(() => {
  const list = [...store.allAssignments].slice(0, 8)
  if (sortBy.value === 'course') list.sort((a, b) => a.course.localeCompare(b.course))
  if (sortBy.value === 'status') list.sort((a, b) => a.status.localeCompare(b.status))
  return list
})
</script>

<style scoped>
.sort-select {
  font-size: 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 3px 8px;
  background: var(--bg);
  color: var(--text-secondary);
  font-family: var(--font-body);
  outline: none;
  cursor: pointer;
}

.assignment-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 0; border-bottom: 1px solid var(--border-soft);
}
.assignment-item:last-child { border-bottom: none; padding-bottom: 0; }

.assignment-color {
  width: 3px; border-radius: 99px;
  align-self: stretch; flex-shrink: 0; min-height: 36px;
}

.assignment-body  { flex: 1; }
.assignment-title { font-size: 13.5px; font-weight: 500; margin-bottom: 3px; }
.assignment-course { font-size: 12px; color: var(--text-muted); }
.assignment-meta  { display: flex; align-items: center; gap: 8px; margin-top: 6px; }

.deadline-badge {
  font-size: 11px; font-weight: 500;
  padding: 2px 7px; border-radius: 99px;
}
.deadline-soon    { background: var(--warning-bg); color: var(--warning); }
.deadline-ok      { background: var(--success-bg); color: var(--success); }
.deadline-overdue { background: var(--danger-bg);  color: var(--danger);  }
</style>
