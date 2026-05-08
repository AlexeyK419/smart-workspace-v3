<template>
  <div class="course-hero card">
    <div class="course-icon" :style="{ background: course.color + '20' }">
      {{ course.emoji }}
    </div>

    <div class="course-hero-info">
      <div class="course-hero-name">{{ course.name }}</div>
      <div class="course-hero-meta">{{ course.teacher }} · {{ course.semester }}</div>
      <div class="course-hero-badges">
        <span class="badge">{{ assignmentsCount }}</span>
        <span class="badge badge-active">Активный</span>
      </div>
    </div>

    <div class="course-actions">
      <button class="btn btn-ghost btn-sm" @click="$emit('edit')">
        <svg viewBox="0 0 24 24" fill="currentColor" style="width:13px;height:13px">
          <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
        </svg>
        Редактировать
      </button>
      <button class="btn btn-ghost btn-sm btn-danger-text" @click="$emit('delete')">
        <svg viewBox="0 0 24 24" fill="currentColor" style="width:13px;height:13px">
          <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
        </svg>
        Удалить
      </button>
    </div>

    <div class="course-progress">
      <div class="course-progress-label">Прогресс курса</div>
      <div class="course-progress-value">{{ progress }}%</div>
      <div class="progress-bar" style="width: 120px; margin-left: auto">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { formatCountRu } from '@/utils/pluralize'

const store = useWorkspaceStore()

const props = defineProps({
  course: { type: Object, required: true },
})

const progress = computed(() => store.getCourseProgress(props.course))
const assignmentsCount = computed(() => formatCountRu((props.course.assignments || []).length, 'задание', 'задания', 'заданий'))

defineEmits(['edit', 'delete'])
</script>

<style scoped>
.course-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.course-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.course-hero-info {
  flex: 1;
  min-width: 200px;
}

.course-hero-name {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 3px;
  letter-spacing: -0.3px;
}

.course-hero-meta {
  font-size: 13px;
  color: var(--text-muted);
}

.course-hero-badges {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.badge {
  font-size: 11.5px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 99px;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  background: var(--surface-2);
}

.badge-active {
  background: var(--success-bg);
  color: var(--success);
  border-color: transparent;
}

.course-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

.btn-danger-text:hover {
  color: var(--danger);
  border-color: var(--danger);
}

.course-progress {
  text-align: right;
}

.course-progress-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.course-progress-value {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
}

@media (max-width: 760px) {
  .course-hero {
    align-items: flex-start;
    gap: 14px;
    padding: 18px;
    border-radius: 24px;
    position: relative;
  }

  .course-icon {
    width: 64px;
    height: 64px;
    border-radius: 18px;
    font-size: 28px;
  }

  .course-hero-info {
    min-width: 0;
  }

  .course-hero-name {
    font-size: 28px;
    line-height: 1.1;
  }

  .course-actions {
    width: 100%;
    order: 4;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .course-progress {
    width: 100%;
    text-align: left;
    order: 3;
    padding-top: 12px;
    border-top: 1px solid var(--border-soft);
  }

  .course-progress-value {
    float: right;
    margin-top: -28px;
    font-size: 30px;
  }

  .course-progress .progress-bar {
    width: 100% !important;
    margin-left: 0 !important;
    margin-top: 12px;
    height: 6px;
  }
}
</style>
