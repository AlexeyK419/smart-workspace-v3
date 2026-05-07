<template>
  <div class="modal-overlay" @click.self="handleClose">
    <div class="modal" :class="{ wide: mode === 'view' && hasFiles }">
      <div class="modal-header">
        <div class="modal-title">{{ modeTitle }}</div>
        <button class="modal-close" @click="handleClose">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="modal-body">
        <!-- ===== CREATE / EDIT MODE ===== -->
        <template v-if="mode === 'create' || mode === 'edit'">
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
            <textarea class="form-input" v-model="form.description" rows="3" placeholder="Краткое описание задания..."></textarea>
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
              <label class="form-label">Прикрепить файлы (опционально)</label>
              <div class="file-upload-area">
                <label class="file-pick-label">
                  <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px"><path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/></svg>
                  {{ form.files.length ? `Выбрано: ${form.files.length} файл(ов)` : 'Выбрать файлы' }}
                  <input type="file" class="file-input" multiple @change="onFilesSelected" />
                </label>
                <div v-if="form.files.length" class="file-chips">
                  <span v-for="(f, i) in form.files" :key="i" class="file-chip">
                    {{ f.name }}
                    <button class="file-chip-remove" @click="removeFile(i)">&times;</button>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ===== VIEW MODE ===== -->
        <template v-if="mode === 'view'">
          <div class="detail-meta">
            <span class="chip" :class="'chip-' + assignment.status">{{ store.statusLabel(assignment.status) }}</span>
            <span v-if="assignment.deadline" class="meta-deadline">
              <svg viewBox="0 0 24 24" fill="currentColor" style="width:12px;height:12px"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/></svg>
              {{ assignment.deadline }}
            </span>
          </div>

          <div v-if="assignment.description" class="detail-desc">{{ assignment.description }}</div>

          <div v-if="assignment.ai_advice" class="ac-ai-saved">💡 AI-подсказка сохранена</div>

          <div class="files-section">
            <div class="files-header">
              <span class="files-title">📎 Файлы ({{ assignment.files?.length || 0 }})</span>
              <label class="upload-btn">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
                Добавить файл
                <input type="file" class="file-hidden-input" @change="handleFileUpload" />
              </label>
            </div>
            <div v-if="!assignment.files?.length" class="files-empty">Файлы не прикреплены</div>
            <div v-else class="files-list">
              <div v-for="file in assignment.files" :key="file.id" class="file-row">
                <div class="file-icon" :style="{ background: file.icon_bg }">{{ file.icon }}</div>
                <div class="file-info">
                  <button class="file-link" @click="previewFile(file)">{{ file.name }}</button>
                  <span class="file-size">{{ store.humanSize(file.size_bytes) }}</span>
                </div>
                <div class="file-actions">
                  <button class="ac-btn" title="Скачать" @click="downloadFile(file)">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
                  </button>
                  <button class="ac-btn ac-btn-del" title="Удалить" @click="deleteFile(file)">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- ===== FOOTER ===== -->
      <template v-if="mode === 'create' || mode === 'edit'">
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="handleCancel">Отмена</button>
          <button class="btn btn-primary" :disabled="!form.title || saving" @click="handleSave">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </template>
      <template v-if="mode === 'view'">
        <div class="modal-footer">
          <div class="footer-left">
            <button class="btn btn-ghost ac-btn-ai" @click="emit('ai-help', assignment)">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
              AI помощь
            </button>
            <button class="btn btn-ghost" @click="startEdit">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
              Редактировать
            </button>
            <button class="btn btn-ghost ac-btn-del" @click="handleDelete">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
              Удалить
            </button>
          </div>
          <button class="btn btn-ghost" @click="emit('close')">Закрыть</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { api } from '@/api/index.js'

const props = defineProps({
  assignment: { type: Object, default: null },
  courseId: { type: Number, required: true },
})
const emit = defineEmits(['close', 'ai-help', 'preview', 'refresh'])

const store = useWorkspaceStore()

const mode = ref(props.assignment ? 'view' : 'create')
const saving = ref(false)
const form = reactive({ title: '', description: '', deadline_raw: '', status: 'pending', files: [] })

const hasFiles = computed(() => props.assignment?.files?.length > 0)
const modeTitle = computed(() => {
  if (mode.value === 'create') return 'Новое задание'
  if (mode.value === 'edit') return 'Редактировать задание'
  return props.assignment?.title || ''
})

function initForm() {
  if (props.assignment) {
    Object.assign(form, {
      title: props.assignment.title,
      description: props.assignment.description,
      deadline_raw: '',
      status: props.assignment.status,
      files: [],
    })
  } else {
    Object.assign(form, { title: '', description: '', deadline_raw: '', status: 'pending', files: [] })
  }
}

watch(() => props.assignment, initForm, { immediate: true })

function startEdit() {
  initForm()
  mode.value = 'edit'
}

function handleCancel() {
  if (mode.value === 'edit') {
    mode.value = 'view'
  } else {
    emit('close')
  }
}

function handleClose() {
  if (mode.value === 'edit' || mode.value === 'create') {
    handleCancel()
  } else {
    emit('close')
  }
}

function onFilesSelected(e) {
  const selected = Array.from(e.target.files || [])
  form.files = [...form.files, ...selected]
  e.target.value = ''
}

function removeFile(index) {
  form.files.splice(index, 1)
}

function formatDeadline(raw) {
  if (!raw) return ''
  const d = new Date(raw)
  const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

async function handleSave() {
  if (!form.title) return
  saving.value = true
  const fd = new FormData()
  fd.append('title', form.title)
  fd.append('description', form.description)
  fd.append('deadline', formatDeadline(form.deadline_raw) || '')
  fd.append('status', form.status)
  if (form.files.length) {
    for (const fileItem of form.files) {
      fd.append('files', fileItem)
    }
  }

  try {
    if (mode.value === 'create') {
      await store.createAssignment(props.courseId, fd)
    } else {
      fd.append('replace_files', 'false')
      await store.updateAssignmentFull(props.courseId, props.assignment.id, fd)
    }
    emit('refresh')
    emit('close')
  } catch (e) {
    store.showToast('Ошибка: ' + (e.message || ''))
  }
  saving.value = false
}

async function handleDelete() {
  if (!confirm('Удалить задание?')) return
  await store.deleteAssignment(props.courseId, props.assignment.id)
  emit('refresh')
  emit('close')
}

async function handleFileUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    await store.uploadAssignmentFile(props.courseId, props.assignment.id, file)
  } catch (e) {
    store.showToast('Ошибка загрузки: ' + e.message)
  }
  e.target.value = ''
}

function previewFile(file) {
  emit('preview', {
    id: file.id,
    name: file.name,
    size: store.humanSize(file.size_bytes),
    icon: file.icon,
    iconBg: file.icon_bg,
    mimeType: file.mime_type,
    date: '—',
    entityType: 'assignmentFile',
    courseId: props.courseId,
    projectId: props.assignment.id,
  })
}

async function downloadFile(file) {
  try {
    await api.downloadAssignmentFile(props.courseId, props.assignment.id, file.id, file.name)
  } catch (e) {
    store.showToast('Ошибка скачивания: ' + e.message)
  }
}

async function deleteFile(file) {
  if (!confirm(`Удалить файл «${file.name}»?`)) return
  await store.deleteAssignmentFile(props.courseId, props.assignment.id, file.id)
}
</script>

<style scoped>
.modal.wide { width: min(680px, 100%); }

.detail-meta { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.meta-deadline { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 4px; }
.detail-desc { font-size: 13px; line-height: 1.6; color: var(--text-secondary); margin-bottom: 16px; white-space: pre-wrap; }
.ac-ai-saved { font-size: 11px; color: #1a7a32; background: #e8f5e9; border-radius: 6px; padding: 4px 8px; margin-bottom: 12px; display: inline-block; }

.files-section { margin-top: 16px; border-top: 1px solid var(--border-soft); padding-top: 14px; }
.files-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.files-title { font-size: 13px; font-weight: 600; }
.files-empty { font-size: 12.5px; color: var(--text-muted); padding: 12px 0; }
.files-list { display: flex; flex-direction: column; gap: 6px; max-height: 300px; overflow-y: auto; }
.file-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: var(--radius-sm);
  border: 1px solid var(--border-soft); background: var(--bg);
}
.file-icon {
  width: 28px; height: 28px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0;
}
.file-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.file-link {
  background: none; border: none; cursor: pointer; padding: 0;
  font-size: 12.5px; font-weight: 500; color: var(--accent); text-align: left;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-family: var(--font-body);
}
.file-link:hover { text-decoration: underline; }
.file-size { font-size: 11px; color: var(--text-muted); }
.file-actions { display: flex; gap: 4px; }

.upload-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 10px; border-radius: var(--radius-sm);
  border: 1px solid var(--accent-mid); background: var(--accent-light);
  font-size: 11.5px; font-weight: 500; cursor: pointer;
  transition: all var(--transition); font-family: var(--font-body);
  color: var(--accent); text-decoration: none;
}
.upload-btn:hover { background: var(--accent); color: white; }
.upload-btn svg { width: 12px; height: 12px; }
.file-hidden-input { display: none; }

.footer-left { display: flex; gap: 6px; }

.form-row { display: flex; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.form-label { font-size: 12px; font-weight: 500; color: var(--text-secondary); }
.form-input {
  width: 100%; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 7px 10px; font-size: 13px; background: var(--bg);
  color: var(--text-primary); font-family: var(--font-body);
  outline: none; transition: border-color var(--transition);
}
.form-input:focus { border-color: var(--accent); }
textarea.form-input { resize: vertical; }

.file-upload-area { display: flex; flex-direction: column; gap: 6px; }
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
.file-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.file-chip {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; padding: 2px 8px; border-radius: 4px;
  background: var(--accent-light); color: var(--accent);
  border: 1px solid var(--accent-mid);
}
.file-chip-remove {
  background: none; border: none; cursor: pointer; font-size: 13px;
  color: var(--accent); padding: 0; line-height: 1;
}

.ac-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 9px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: transparent;
  font-size: 11.5px; font-weight: 500; cursor: pointer;
  transition: all var(--transition); font-family: var(--font-body);
  color: var(--text-muted);
}
.ac-btn:hover { background: var(--surface-2); color: var(--text-primary); }
.ac-btn svg { width: 12px; height: 12px; }
.ac-btn-ai { border-color: var(--accent-mid); color: var(--accent); background: var(--accent-light); }
.ac-btn-ai:hover { background: var(--accent); color: white; }
.ac-btn-del:hover { color: var(--danger); border-color: var(--danger); background: var(--danger-bg); }

.modal-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-top: 1px solid var(--border-soft);
}
.footer-left { display: flex; gap: 6px; }

@media (max-width: 760px) {
  .form-row { flex-direction: column; gap: 0; }
  .footer-left { display: grid; grid-template-columns: 1fr 1fr; width: 100%; }
  .modal-footer { flex-direction: column; gap: 8px; }
  .modal-footer > button:last-child { width: 100%; }
}
</style>
