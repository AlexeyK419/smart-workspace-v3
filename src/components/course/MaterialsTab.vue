<template>
  <div>
    <!-- Header -->
    <div class="files-header">
      <div class="files-count">{{ course.materials?.length ?? 0 }} файлов</div>
      <label class="btn btn-primary upload-label">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/></svg>
        <span>{{ uploading ? 'Загрузка...' : 'Загрузить файл' }}</span>
        <input type="file" class="file-input" @change="onFileChange" :disabled="uploading" />
      </label>
    </div>

    <!-- Empty -->
    <div v-if="!course.materials?.length" class="empty-state">
      <div class="empty-icon">📂</div>
      <p>Материалы ещё не загружены.<br/>Нажмите «Загрузить файл», чтобы добавить первый.</p>
    </div>

    <!-- File list -->
    <div v-for="file in course.materials" :key="file.id" class="file-row">
      <div class="file-icon" :style="{ background: file.icon_bg }">{{ file.icon }}</div>
      <div class="file-info">
        <div class="file-name">{{ file.name }}</div>
        <div class="file-meta">{{ store.humanSize(file.size_bytes) }} · {{ formatDate(file.created_at) }}</div>
      </div>
      <div class="file-actions">
        <a :href="api.downloadMaterialUrl(course.id, file.id)" target="_blank" class="action-btn" title="Скачать">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
        </a>
        <button class="action-btn action-btn-danger" title="Удалить" @click="remove(file.id)">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { api } from '@/api/index.js'

const props    = defineProps({ course: { type: Object, required: true } })
const store    = useWorkspaceStore()
const uploading = ref(false)

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  await store.uploadMaterial(props.course.id, file)
  uploading.value = false
  e.target.value = ''
}

async function remove(matId) {
  if (!confirm('Удалить материал?')) return
  await store.deleteMaterial(props.course.id, matId)
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.files-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.files-count  { font-size: 14px; font-weight: 600; }

.upload-label { cursor: pointer; position: relative; }
.file-input   { position: absolute; opacity: 0; width: 0; height: 0; }

.empty-state { text-align: center; padding: 48px 20px; color: var(--text-muted); }
.empty-icon  { font-size: 36px; margin-bottom: 10px; }
.empty-state p { font-size: 13.5px; line-height: 1.6; }

.file-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: var(--radius-sm);
  border: 1px solid var(--border-soft); background: var(--surface);
  margin-bottom: 8px;
  transition: border-color var(--transition), box-shadow var(--transition);
}
.file-row:hover { border-color: var(--accent-mid); box-shadow: var(--shadow); }

.file-icon {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; flex-shrink: 0;
}
.file-info { flex: 1; min-width: 0; }
.file-name { font-size: 13.5px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-meta { font-size: 11.5px; color: var(--text-muted); }

.file-actions { display: flex; gap: 6px; }
.action-btn {
  width: 30px; height: 30px; border-radius: 6px;
  border: 1px solid var(--border); background: transparent;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all var(--transition); text-decoration: none; color: var(--text-muted);
}
.action-btn:hover { background: var(--surface-2); color: var(--accent); border-color: var(--accent-mid); }
.action-btn svg { width: 14px; height: 14px; }
.action-btn-danger:hover { color: var(--danger); border-color: var(--danger); background: var(--danger-bg); }
</style>
