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

    <div v-for="a in sorted" :key="a.id" class="assignment-item" @click="openDetail(a)">
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
      <div class="assignment-arrow">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
      </div>
    </div>

    <!-- Assignment Detail Modal -->
    <div v-if="selectedAssignment" class="modal-overlay" @click.self="selectedAssignment = null">
      <div class="modal assignment-detail-modal">
        <div class="modal-header">
          <div class="modal-title">Информация о задании</div>
          <button class="modal-close" @click="selectedAssignment = null">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <div class="detail-label">Название</div>
            <div class="detail-value detail-title">{{ selectedAssignment.title }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">Курс</div>
            <div class="detail-value">
              <span class="course-badge" :style="{ background: selectedAssignment.courseColor + '20', color: selectedAssignment.courseColor }">
                {{ selectedAssignment.course }}
              </span>
            </div>
          </div>
          <div class="detail-row" v-if="selectedAssignment.description">
            <div class="detail-label">Описание</div>
            <div class="detail-value detail-desc">{{ selectedAssignment.description }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">Дедлайн</div>
            <div class="detail-value">
              <span class="deadline-badge" :class="store.urgencyClass(selectedAssignment.deadline)">
                📅 {{ selectedAssignment.deadline }}
              </span>
            </div>
          </div>
          <div class="detail-row">
            <div class="detail-label">Статус</div>
            <div class="detail-value">
              <span class="chip" :class="'chip-' + selectedAssignment.status">
                {{ store.statusLabel(selectedAssignment.status) }}
              </span>
            </div>
          </div>
          <div class="detail-row" v-if="selectedAssignment.file_name">
            <div class="detail-label">Прикреплённый файл</div>
            <div class="detail-value">
              <span class="file-badge">📎 {{ selectedAssignment.file_name }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="selectedAssignment = null">Закрыть</button>
          <button class="btn btn-primary" @click="goToCourse">Перейти к курсу</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
const router = useRouter()
const sortBy = ref('date')
const selectedAssignment = ref(null)

const sorted = computed(() => {
  const list = [...store.allAssignments].slice(0, 8)
  if (sortBy.value === 'course') list.sort((a, b) => a.course.localeCompare(b.course))
  if (sortBy.value === 'status') list.sort((a, b) => a.status.localeCompare(b.status))
  return list
})

function openDetail(assignment) {
  selectedAssignment.value = assignment
}

function goToCourse() {
  const course = store.courses.find(c => c.name === selectedAssignment.value.course)
  if (course) {
    selectedAssignment.value = null
    router.push(`/course/${course.id}`)
  }
}
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
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-soft);
  cursor: pointer;
  transition: background var(--transition);
  margin: 0 -10px;
  padding-left: 10px;
  padding-right: 10px;
  border-radius: var(--radius-sm);
}

.assignment-item:hover {
  background: var(--surface-2);
}

.assignment-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.assignment-color {
  width: 3px;
  border-radius: 99px;
  align-self: stretch;
  flex-shrink: 0;
  min-height: 36px;
}

.assignment-body {
  flex: 1;
}

.assignment-title {
  font-size: 13.5px;
  font-weight: 500;
  margin-bottom: 3px;
}

.assignment-course {
  font-size: 12px;
  color: var(--text-muted);
}

.assignment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.assignment-arrow {
  display: flex;
  align-items: center;
  color: var(--text-muted);
  opacity: 0;
  transition: opacity var(--transition);
}

.assignment-item:hover .assignment-arrow {
  opacity: 1;
}

.assignment-arrow svg {
  width: 18px;
  height: 18px;
}

.deadline-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: 99px;
}

.deadline-soon {
  background: var(--warning-bg);
  color: var(--warning);
}

.deadline-ok {
  background: var(--success-bg);
  color: var(--success);
}

.deadline-overdue {
  background: var(--danger-bg);
  color: var(--danger);
}

/* Modal styles */
.assignment-detail-modal {
  max-width: 480px;
}

.detail-row {
  margin-bottom: 16px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.detail-value {
  font-size: 14px;
  color: var(--text-primary);
}

.detail-title {
  font-weight: 600;
  font-size: 16px;
}

.detail-desc {
  line-height: 1.6;
  color: var(--text-secondary);
}

.course-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.file-badge {
  display: inline-block;
  padding: 4px 10px;
  background: var(--surface-2);
  border-radius: 6px;
  font-size: 13px;
}
</style>