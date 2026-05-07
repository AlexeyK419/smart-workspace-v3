<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal" :class="{ wide: isPdf }">
      <div class="modal-header">
        <div style="display: flex; align-items: center; gap: 10px">
          <div class="file-icon" :style="{ background: file.iconBg }">{{ file.icon }}</div>
          <div class="modal-title">{{ file.name }}</div>
        </div>
        <button class="modal-close" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="modal-body" :class="{ noPad: isPdf || isImage }">
        <div class="file-meta-row" v-if="!loading && !error">
          <span>{{ file.size }}</span>
          <span v-if="file.date">{{ file.date }}</span>
          <span>{{ file.type || mimeLabel }}</span>
        </div>

        <div v-if="loading" class="preview-loading">Загрузка содержимого...</div>
        <div v-else-if="error" class="preview-error">{{ error }}</div>

        <embed v-else-if="isPdf && blobUrl" :src="blobUrl" type="application/pdf" class="pdf-viewer" />

        <img v-else-if="isImage && blobUrl" :src="blobUrl" class="image-viewer" />

        <div v-else-if="isDocx && docxHtml" class="docx-preview" v-html="docxHtml" />

        <pre v-else class="file-preview">{{ previewText }}</pre>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="emit('close')">Закрыть</button>
        <button class="btn btn-primary" @click="emit('download')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
          Скачать
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api, fetchBlobUrl, getDownloadPath } from '@/api/index.js'
import mammoth from 'mammoth'

const props = defineProps({ file: { type: Object, required: true } })
const emit = defineEmits(['close', 'download'])

const loading = ref(true)
const error = ref('')
const previewText = ref('')
const blobUrl = ref('')
const docxHtml = ref('')

const mimeLabel = computed(() => {
  const m = props.file.mimeType || ''
  const map = { 'application/pdf': 'PDF', 'image/': 'IMG',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'application/msword': 'DOC', 'application/vnd.oasis.opendocument.text': 'ODT',
    'text/plain': 'TXT' }
  for (const [k, v] of Object.entries(map)) { if (m.startsWith(k)) return v }
  return m.split('/')[1]?.toUpperCase() || 'FILE'
})

const isPdf = computed(() => (props.file.mimeType || '').includes('pdf'))
const isImage = computed(() => (props.file.mimeType || '').startsWith('image/'))
const isDocx = computed(() =>
  (props.file.mimeType || '').includes('wordprocessingml') ||
  (props.file.mimeType || '').includes('msword')
)

onMounted(async () => {
  try {
    if (isPdf.value || isImage.value) {
      const path = getDownloadPath(props.file.entityType, props.file.courseId, props.file.projectId, props.file.id)
      blobUrl.value = await fetchBlobUrl(path)
      previewText.value = ''
    } else if (isDocx.value) {
      const path = getDownloadPath(props.file.entityType, props.file.courseId, props.file.projectId, props.file.id)
      const docxHtmlResult = await fetchAndConvertDocx(path)
      docxHtml.value = docxHtmlResult
      previewText.value = ''
    } else {
      let data
      if (props.file.entityType === 'material') {
        data = await api.previewMaterial(props.file.courseId, props.file.id)
      } else if (props.file.entityType === 'assignment') {
        data = await api.previewAssignment(props.file.courseId, props.file.id)
      } else if (props.file.entityType === 'assignmentFile') {
        data = await api.previewAssignmentFile(props.file.courseId, props.file.projectId, props.file.id)
      } else if (props.file.entityType === 'projectFile') {
        data = await api.previewProjectFile(props.file.projectId, props.file.id)
      }
      previewText.value = data?.text || ''
    }
  } catch (e) {
    error.value = e.message || 'Не удалось загрузить содержимое'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (blobUrl.value) {
    window.URL.revokeObjectURL(blobUrl.value)
    blobUrl.value = ''
  }
})

const BASE = 'http://localhost:8000'
const AUTH_TOKEN_KEY = 'workspace_token'

async function fetchAndConvertDocx(downloadPath) {
  const token = localStorage.getItem(AUTH_TOKEN_KEY) || ''
  const headers = token ? { Authorization: `Bearer ${token}` } : {}
  const res = await fetch(`${BASE}${downloadPath}`, { headers })
  if (!res.ok) throw new Error('Не удалось загрузить DOCX')
  const arrayBuffer = await res.arrayBuffer()
  const result = await mammoth.convertToHtml({ arrayBuffer })
  return result.value
}
</script>

<style scoped>
.modal-overlay { z-index: 200; }
.file-icon {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.file-meta-row {
  display: flex; gap: 16px; margin-bottom: 16px;
  font-size: 12.5px; color: var(--text-muted);
}
.file-preview {
  font-size: 13px; line-height: 1.8; color: var(--text-secondary);
  white-space: pre-wrap; font-family: 'Courier New', monospace;
  background: var(--bg); border-radius: 8px; padding: 16px;
  border: 1px solid var(--border-soft);
  max-height: 60vh; overflow: auto;
}
.preview-loading {
  text-align: center; padding: 32px;
  color: var(--text-muted); font-size: 13px;
}
.preview-error {
  text-align: center; padding: 32px;
  color: var(--danger); font-size: 13px;
}
.pdf-viewer {
  width: 100%; height: 75vh; border: none;
  border-radius: 8px;
}
.image-viewer {
  max-width: 100%; max-height: 70vh;
  display: block; margin: 0 auto; border-radius: 8px;
}
.docx-preview {
  font-size: 14px; line-height: 1.7; color: var(--text-primary);
  padding: 16px 20px; max-height: 60vh; overflow: auto;
}
.docx-preview :deep(h1) { font-size: 1.5em; margin: 0.6em 0 0.3em; }
.docx-preview :deep(h2) { font-size: 1.3em; margin: 0.5em 0 0.2em; }
.docx-preview :deep(h3) { font-size: 1.15em; margin: 0.4em 0 0.2em; }
.docx-preview :deep(p) { margin: 0.4em 0; }
.docx-preview :deep(ul), .docx-preview :deep(ol) { padding-left: 1.5em; margin: 0.4em 0; }
.docx-preview :deep(table) { border-collapse: collapse; width: 100%; margin: 0.5em 0; }
.docx-preview :deep(td), .docx-preview :deep(th) { border: 1px solid var(--border); padding: 6px 10px; }
.docx-preview :deep(img) { max-width: 100%; height: auto; }
.noPad { padding: 0; }
.modal.wide { width: min(960px, 100%); }
</style>
