<template>
  <div>
    <!-- Header + Add button -->
    <div class="tab-header">
      <div class="tab-count">{{ course.assignments?.length ?? 0 }} заданий</div>
      <button class="btn btn-primary" @click="openAddForm">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
        Добавить задание
      </button>
    </div>

    <!-- Add / Edit Assignment Form (inline) -->
    <Transition name="form-slide">
      <div v-if="showForm" class="add-form card">
        <div class="add-form-title">{{ editingId ? 'Редактировать задание' : 'Новое задание' }}</div>
        <div class="form-row">
          <div class="form-group" style="flex:2">
            <label class="form-label">Название *</label>
            <input class="form-input" v-model="form.title" placeholder="Например: Лабораторная работа №5" />
          </div>
          <div class="form-group" style="flex:1">
            <label class="form-label">Дедлайн</label>
            <input class="form-input" type="date" v-model="form.deadline_raw" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Описание</label>
          <textarea class="form-input" v-model="form.description" rows="2" placeholder="Краткое описание задания..."></textarea>
        </div>
        <div class="form-row" style="align-items:flex-end">
          <div class="form-group" style="flex:1">
            <label class="form-label">Статус</label>
            <select class="form-input" v-model="form.status">
              <option value="pending">Ожидает</option>
              <option value="progress">В процессе</option>
              <option value="done">Сдано</option>
            </select>
          </div>
          <div class="form-group" style="flex:2">
            <label class="form-label">Прикрепить файл (опционально)</label>
            <label class="file-pick-label">
              <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px"><path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/></svg>
              {{ form.file ? form.file.name : 'Выбрать файл' }}
              <input type="file" class="file-input" @change="e => form.file = e.target.files[0]" />
            </label>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-ghost" @click="cancelForm">Отмена</button>
          <button class="btn btn-primary" :disabled="!form.title || saving" @click="submitForm">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            {{ saving ? 'Сохранение...' : (editingId ? 'Сохранить' : 'Создать') }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- Empty -->
    <div v-if="!course.assignments?.length && !showForm" class="empty-state">
      <div class="empty-icon">📋</div>
      <p>Заданий пока нет. Добавьте первое!</p>
    </div>

    <!-- Assignment cards -->
    <div class="assignments-grid">
      <div v-for="a in course.assignments" :key="a.id" class="assignment-card">
        <div class="ac-top">
          <div class="ac-title">{{ a.title }}</div>
          <div style="display:flex;gap:6px;align-items:center">
            <select class="status-select" :value="a.status" @change="changeStatus(a, $event)">
              <option value="pending">Ожидает</option>
              <option value="progress">В процессе</option>
              <option value="done">Сдано</option>
              <option value="overdue">Просрочено</option>
            </select>
            <span class="chip" :class="'chip-' + a.status">{{ store.statusLabel(a.status) }}</span>
          </div>
        </div>

        <div class="ac-desc">{{ a.description }}</div>

        <!-- Saved AI advice preview -->
        <div v-if="a.ai_advice" class="ac-ai-saved">
          💡 AI-подсказка сохранена
        </div>

        <div class="ac-footer">
          <div class="ac-deadline" v-if="a.deadline">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width:12px;height:12px"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/></svg>
            {{ a.deadline }}
          </div>
          <div style="display:flex;gap:6px;margin-left:auto">
            <button v-if="a.file_name" class="ac-btn" title="Скачать файл" @click="downloadAssignment(a)">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
              {{ a.file_name }}
            </button>
            <button class="ac-btn" title="Редактировать" @click="openEditForm(a)">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
            </button>
            <button class="ac-btn ac-btn-ai" @click="emit('ai-help', a)">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
              AI
            </button>
            <button class="ac-btn ac-btn-del" title="Удалить" @click="remove(a.id)">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { api } from '@/api/index.js'

const props = defineProps({ course: { type: Object, required: true } })
const emit  = defineEmits(['ai-help'])
const store = useWorkspaceStore()

const showForm  = ref(false)
const saving    = ref(false)
const editingId = ref(null)
const form = reactive({ title: '', description: '', deadline_raw: '', status: 'pending', file: null })

function openAddForm() {
  editingId.value = null
  Object.assign(form, { title: '', description: '', deadline_raw: '', status: 'pending', file: null })
  showForm.value = true
}

function openEditForm(a) {
  editingId.value = a.id
  Object.assign(form, {
    title: a.title,
    description: a.description,
    deadline_raw: '',
    status: a.status,
    file: null,
  })
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  editingId.value = null
  Object.assign(form, { title: '', description: '', deadline_raw: '', status: 'pending', file: null })
}

function formatDeadline(raw) {
  if (!raw) return ''
  const d = new Date(raw)
  const months = ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

async function submitForm() {
  if (!form.title) return
  saving.value = true
  const fd = new FormData()
  fd.append('title',       form.title)
  fd.append('description', form.description)
  fd.append('deadline',    formatDeadline(form.deadline_raw) || (editingId.value ? '' : ''))
  fd.append('status',      form.status)
  if (form.file) fd.append('file', form.file)

  if (editingId.value) {
    await store.updateAssignmentFull(props.course.id, editingId.value, fd)
  } else {
    await store.createAssignment(props.course.id, fd)
  }
  saving.value = false
  cancelForm()
}

async function changeStatus(a, e) {
  await store.updateAssignmentStatus(props.course.id, a.id, e.target.value)
}

async function downloadAssignment(assignment) {
  try {
    await api.downloadAssignment(props.course.id, assignment.id, assignment.file_name || assignment.title)
  } catch (e) {
    store.showToast('Ошибка скачивания: ' + e.message)
  }
}

async function remove(id) {
  if (!confirm('Удалить задание?')) return
  await store.deleteAssignment(props.course.id, id)
}
</script>

<style scoped>
.tab-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.tab-count  { font-size: 14px; font-weight: 600; }
.add-form { margin-bottom: 16px; padding: 18px; border: 1.5px solid var(--accent-mid); }
.add-form-title { font-weight: 600; font-size: 14px; margin-bottom: 14px; color: var(--accent); }
.form-row { display: flex; gap: 12px; }
.form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }
.file-pick-label {
  display: flex; align-items: center; gap: 7px;
  padding: 8px 12px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); cursor: pointer; font-size: 12.5px;
  color: var(--text-secondary); background: var(--bg);
  transition: border-color var(--transition);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.file-pick-label:hover { border-color: var(--accent); color: var(--accent); }
.file-input { display: none; }
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
}
.assignment-card:hover { box-shadow: var(--shadow); }
.ac-top {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 8px; margin-bottom: 8px;
}
.ac-title { font-size: 13.5px; font-weight: 600; line-height: 1.4; }
.ac-desc  { font-size: 12.5px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.55; }
.ac-ai-saved {
  font-size: 11px; color: #1a7a32; background: #e8f5e9;
  border-radius: 6px; padding: 4px 8px; margin-bottom: 8px;
  display: inline-block;
}
.ac-footer { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.ac-deadline { font-size: 11.5px; color: var(--text-muted); display: flex; align-items: center; gap: 3px; }
.status-select {
  font-size: 11px; border: 1px solid var(--border); border-radius: 4px;
  padding: 2px 4px; background: var(--bg); font-family: var(--font-body);
  color: var(--text-secondary); cursor: pointer; outline: none;
}
.ac-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 9px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: transparent;
  font-size: 11.5px; font-weight: 500; cursor: pointer;
  transition: all var(--transition); font-family: var(--font-body);
  color: var(--text-muted); text-decoration: none;
}
.ac-btn:hover { background: var(--surface-2); color: var(--text-primary); }
.ac-btn svg { width: 12px; height: 12px; }
.ac-btn-ai { border-color: var(--accent-mid); color: var(--accent); background: var(--accent-light); }
.ac-btn-ai:hover { background: var(--accent); color: white; }
.ac-btn-del:hover { color: var(--danger); border-color: var(--danger); background: var(--danger-bg); }
.form-slide-enter-active, .form-slide-leave-active { transition: all 0.25s ease; }
.form-slide-enter-from, .form-slide-leave-to { opacity: 0; transform: translateY(-10px); }

@media (max-width: 760px) {
  .tab-header {
    gap: 12px;
  }

  .tab-header .btn {
    width: 46px;
    min-width: 46px;
    padding: 0;
    overflow: hidden;
    color: transparent;
    gap: 0;
  }

  .tab-header .btn svg {
    color: #fff;
  }

  .add-form,
  .assignment-card {
    border-radius: 20px;
  }

  .form-row {
    flex-direction: column;
    gap: 0;
  }

  .form-actions,
  .assignments-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .ac-top {
    display: grid;
  }

  .ac-footer {
    align-items: stretch;
  }

  .ac-footer > div:last-child {
    width: 100%;
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-left: 0 !important;
  }

  .ac-btn {
    min-height: 38px;
    justify-content: center;
    border-radius: 13px;
  }
}
</style>
