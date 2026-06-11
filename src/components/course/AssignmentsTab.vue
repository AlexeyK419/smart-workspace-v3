<template>
  <div>
    <div class="tab-header">
      <div class="tab-count">{{ formatCountRu(course.assignments?.length ?? 0, 'задание', 'задания', 'заданий') }}</div>
      <button class="btn btn-primary mobile-plus-btn" @click="emit('open-detail', null)">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
        <span class="mobile-plus-label">Добавить задание</span>
      </button>
    </div>

    <div v-if="!course.assignments?.length" class="empty-state">
      <div class="empty-icon">📋</div>
      <p>Заданий пока нет. Добавьте первое!</p>
    </div>

    <div class="assignments-grid">
      <div v-for="a in course.assignments" :key="a.id" class="assignment-card" @click="emit('open-detail', a)">
        <div class="ac-top">
          <div class="ac-title">{{ a.title }}</div>
          <div style="display:flex;align-items:center" @click.stop>
            <select class="status-select chip" :class="'chip-' + a.status" :value="a.status" @change="changeStatus(a, $event)">
              <option value="pending">Ожидает</option>
              <option value="progress">В процессе</option>
              <option value="done">Сдано</option>
              <option value="overdue">Просрочено</option>
            </select>
          </div>
        </div>

        <div class="ac-desc">{{ a.description }}</div>

        <div v-if="a.ai_advice" class="ac-ai-saved">💡 AI-подсказка сохранена</div>

        <div class="ac-footer">
          <div class="ac-deadline" v-if="a.deadline">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width:12px;height:12px"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/></svg>
            {{ a.deadline }}
          </div>
          <div v-if="a.files?.length" class="ac-file-count">📎 {{ a.files.length }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useWorkspaceStore } from '@/stores/workspace'
import { formatCountRu } from '@/utils/pluralize'

const props = defineProps({ course: { type: Object, required: true } })
const emit  = defineEmits(['ai-help', 'open-detail'])
const store = useWorkspaceStore()

async function changeStatus(a, e) {
  await store.updateAssignmentStatus(props.course.id, a.id, e.target.value)
}
</script>

<style scoped>
.tab-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.tab-count  { font-size: 14px; font-weight: 600; }
.empty-state { text-align: center; padding: 48px 20px; color: var(--text-muted); }
.empty-icon  { font-size: 36px; margin-bottom: 10px; }
.empty-state p { font-size: 13.5px; }
.assignments-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 14px;
}
.assignment-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px;
  transition: box-shadow var(--transition);
  cursor: pointer;
}
.assignment-card:hover { box-shadow: var(--shadow); }
.ac-top {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 8px; margin-bottom: 8px;
}
.ac-title { font-size: 13.5px; font-weight: 600; line-height: 1.4; }
.ac-desc  { font-size: 12.5px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.55; }
.ac-file-count {
  font-size: 11px; color: var(--accent); display: flex; align-items: center; gap: 3px;
  margin-left: auto;
}
.ac-ai-saved {
  font-size: 11px; color: #1a7a32; background: #e8f5e9;
  border-radius: 6px; padding: 4px 8px; margin-bottom: 8px;
  display: inline-block;
}
.ac-footer { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.ac-deadline { font-size: 11.5px; color: var(--text-muted); display: flex; align-items: center; gap: 3px; }
.status-select {
  border: 1px solid transparent; 
  padding-right: 20px;
  cursor: pointer; outline: none;
  font-family: var(--font-body);
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22currentColor%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 4px center;
  background-size: 14px;
}
.status-select.chip-pending { border-color: var(--border); }
.status-select option { background: var(--bg); color: var(--text-primary); }

@media (max-width: 760px) {
  .tab-header { gap: 12px; }

  .tab-header .btn {
    width: 46px; min-width: 46px; padding: 0;
    overflow: hidden; color: transparent; gap: 0;
    justify-content: center;
  }

  .mobile-plus-btn svg { display: block; }
  .mobile-plus-label { display: none; }
  .tab-header .btn svg { color: #fff; }

  .assignment-card { border-radius: 20px; }
  .assignments-grid { grid-template-columns: 1fr; display: grid; }
  .ac-top { display: grid; }
}
</style>
