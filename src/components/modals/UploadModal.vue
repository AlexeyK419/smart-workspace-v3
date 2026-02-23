<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal" style="max-width: 420px">
      <div class="modal-header">
        <div class="modal-title">Загрузить материал</div>
        <button class="modal-close" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="drop-zone" @click="store.showToast('Загрузка файлов скоро будет доступна!')">
          <div class="drop-icon">📎</div>
          <div class="drop-title">Нажмите для выбора файла</div>
          <div class="drop-sub">PDF, DOCX, PNG, MP4 — до 50 МБ</div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="emit('close')">Отмена</button>
        <button class="btn btn-primary" disabled style="opacity: .5">Загрузить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useWorkspaceStore } from '@/stores/workspace'
const emit  = defineEmits(['close'])
const store = useWorkspaceStore()
</script>

<style scoped>
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: 12px; padding: 40px;
  text-align: center; cursor: pointer;
  transition: border-color var(--transition), background var(--transition);
}
.drop-zone:hover { border-color: var(--accent); background: var(--accent-light); }
.drop-icon  { font-size: 32px; margin-bottom: 12px; }
.drop-title { font-size: 14px; font-weight: 500; margin-bottom: 6px; }
.drop-sub   { font-size: 12px; color: var(--text-muted); }
</style>
