<template>
  <div class="course-hero card">
    <div class="course-icon" :style="{ background: course.color + '20' }">
      {{ course.emoji }}
    </div>

    <div class="course-hero-info">
      <div class="course-hero-name">{{ course.name }}</div>
      <div class="course-hero-meta">{{ course.teacher }} · {{ course.semester }}</div>
      <div class="course-hero-badges">
        <span class="badge">{{ course.credits }} кредита</span>
        <span class="badge">{{ course.assignments.length }} заданий</span>
        <span class="badge badge-active">Активный</span>
      </div>
    </div>

    <div class="course-progress">
      <div class="course-progress-label">Прогресс курса</div>
      <div class="course-progress-value">{{ course.progress }}%</div>
      <div class="progress-bar" style="width: 120px; margin-left: auto">
        <div class="progress-fill" :style="{ width: course.progress + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  course: { type: Object, required: true },
})
</script>

<style scoped>
.course-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.course-icon {
  width: 52px; height: 52px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; flex-shrink: 0;
}

.course-hero-info { flex: 1; }

.course-hero-name {
  font-family: var(--font-display);
  font-size: 22px; font-weight: 600;
  margin-bottom: 3px; letter-spacing: -0.3px;
}

.course-hero-meta { font-size: 13px; color: var(--text-muted); }

.course-hero-badges { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }

.badge {
  font-size: 11.5px; font-weight: 500;
  padding: 3px 10px; border-radius: 99px;
  border: 1px solid var(--border);
  color: var(--text-secondary); background: var(--surface-2);
}

.badge-active {
  background: var(--success-bg);
  color: var(--success);
  border-color: transparent;
}

.course-progress { text-align: right; }

.course-progress-label {
  font-size: 11px; color: var(--text-muted); margin-bottom: 4px;
}

.course-progress-value {
  font-family: var(--font-display);
  font-size: 24px; font-weight: 700; color: var(--accent);
}
</style>
