<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div style="display:flex;align-items:center;gap:8px">
          <div class="gc-icon">🤖</div>
          <div class="modal-title">GigaChat — AI Помощь</div>
        </div>
        <button class="modal-close" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="modal-body">
        <!-- Assignment info -->
        <div class="task-card">
          <div class="task-label">Задание</div>
          <div class="task-title">{{ assignment.title }}</div>
          <div v-if="assignment.deadline" class="task-deadline">📅 Дедлайн: {{ assignment.deadline }}</div>
        </div>

        <!-- Question input -->
        <div class="form-group" style="margin-top:14px">
          <label class="form-label">Ваш вопрос (необязательно)</label>
          <input class="form-input" v-model="question"
            placeholder="Например: с чего начать? какие источники использовать?" />
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="ai-loading">
          <div class="gc-badge"><span class="gc-dot"></span> GigaChat думает...</div>
          <div class="dots"><span></span><span></span><span></span></div>
        </div>

        <!-- Result -->
        <div v-else-if="advice" class="ai-result">
          <div class="ai-result-header">
            <div class="gc-badge"><span class="gc-dot"></span> Ответ GigaChat</div>
          </div>
          <div class="ai-result-body" v-html="renderedAdvice"></div>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="error-box">⚠️ {{ error }}</div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="emit('close')">Закрыть</button>
        <button class="btn btn-ask" @click="askGigaChat" :disabled="isLoading">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/></svg>
          {{ advice ? '↺ Спросить снова' : 'Спросить GigaChat' }}
        </button>
        <button class="btn btn-ghost" @click="emit('open-chat')">Открыть чат</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '@/api/index.js'

const props = defineProps({ assignment: { type: Object, required: true } })
const emit  = defineEmits(['close', 'open-chat'])

const question  = ref('')
const advice    = ref('')
const error     = ref('')
const isLoading = ref(false)

async function askGigaChat() {
  isLoading.value = true
  advice.value = ''
  error.value  = ''
  try {
    const res = await api.aiAssignmentHelp(props.assignment.id, question.value)
    advice.value = res.advice
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

const renderedAdvice = computed(() => {
  if (!advice.value) return ''
  return advice.value
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`(.+?)`/g,'<code>$1</code>')
    .replace(/^(\d+)\. (.+)$/gm,'<li><span class="n">$1.</span> $2</li>')
    .replace(/^- (.+)$/gm,'<li>$1</li>')
    .replace(/\n/g,'<br/>')
})
</script>

<style scoped>
.gc-icon { font-size: 20px; }

.task-card {
  background: var(--surface-2); border-radius: var(--radius-sm);
  padding: 12px 14px; border-left: 3px solid #1a7a32;
}
.task-label    { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .6px; color: #1a7a32; margin-bottom: 4px; }
.task-title    { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.task-deadline { font-size: 12px; color: var(--text-muted); }

.gc-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11.5px; font-weight: 600; color: #1a7a32;
  background: #e8f5e9; border: 1px solid #a5d6a7;
  border-radius: 99px; padding: 3px 10px;
}
.gc-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #1a7a32; display: inline-block;
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px 0; }
.ai-result  { margin-top: 14px; }
.ai-result-header { margin-bottom: 10px; }
.ai-result-body {
  font-size: 13.5px; line-height: 1.8; color: var(--text-secondary);
  background: var(--bg); border-radius: 8px; padding: 14px;
  border: 1px solid var(--border-soft);
}
.ai-result-body :deep(strong) { font-weight: 600; color: var(--text-primary); }
.ai-result-body :deep(li) { display: flex; gap: 6px; padding: 2px 0; }
.ai-result-body :deep(.n) { color: #1a7a32; font-weight: 600; flex-shrink: 0; }
.ai-result-body :deep(code) { background: var(--border-soft); border-radius: 4px; padding: 1px 5px; font-size: 12px; font-family: monospace; }

.error-box {
  margin-top: 14px; background: var(--danger-bg); color: var(--danger);
  border-radius: 8px; padding: 12px; font-size: 13px;
}

.btn-ask {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 8px 16px; border-radius: var(--radius-sm);
  font-size: 13px; font-weight: 500; cursor: pointer;
  background: linear-gradient(135deg, #1a7a32, #0f5522);
  color: white; border: none; font-family: var(--font-body);
  transition: opacity var(--transition);
}
.btn-ask:hover    { opacity: .9; }
.btn-ask:disabled { opacity: .5; cursor: wait; }
</style>
