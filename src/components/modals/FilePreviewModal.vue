<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div style="display: flex; align-items: center; gap: 10px">
          <div class="file-icon" :style="{ background: file.iconBg }">{{ file.icon }}</div>
          <div class="modal-title">{{ file.name }}</div>
        </div>
        <button class="modal-close" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="file-meta-row">
          <span>📁 {{ file.size }}</span>
          <span>📅 {{ file.date }}</span>
          <span>📄 {{ file.type }}</span>
        </div>
        <pre class="file-preview">{{ file.preview }}</pre>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="emit('close')">Закрыть</button>
        <button class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
          Скачать
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ file: { type: Object, required: true } })
const emit = defineEmits(['close'])
</script>

<style scoped>
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
}
</style>
