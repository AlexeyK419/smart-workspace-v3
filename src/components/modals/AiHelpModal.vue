<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal ai-help-modal">
      <div class="modal-header">
        <div class="modal-title">
          <span class="ai-icon">🤖</span>
          AI-помощник по заданию
        </div>
        <button class="modal-close" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="modal-body">
        <!-- Assignment info -->
        <div class="assignment-info">
          <div class="assignment-info-title">{{ assignment.title }}</div>
          <div class="assignment-info-desc" v-if="assignment.description">{{ assignment.description }}</div>
          <div class="assignment-info-meta">
            <span v-if="assignment.deadline">📅 {{ assignment.deadline }}</span>
            <span class="chip" :class="'chip-' + assignment.status">{{ statusLabel(assignment.status) }}</span>
          </div>
        </div>

        <!-- Question input -->
        <div class="question-section">
          <label class="form-label">Ваш вопрос (необязательно)</label>
          <textarea 
            class="form-input question-input" 
            v-model="question" 
            rows="2"
            placeholder="Например: не понимаю с чего начать, как подойти к решению..."
            :disabled="isLoading"
          ></textarea>
        </div>

        <!-- Loading state -->
        <div v-if="isLoading" class="loading-state">
          <div class="gigachat-badge">
            <span class="gc-dot"></span>
            GigaChat
          </div>
          <div class="dots"><span></span><span></span><span></span></div>
          <span>Анализирует задание и готовит подсказки...</span>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-state">
          <div class="error-icon">⚠️</div>
          <div class="error-title">Ошибка</div>
          <div class="error-msg">{{ error }}</div>
          <button class="btn btn-ghost" style="margin-top:12px" @click="error = ''">Попробовать снова</button>
        </div>

        <!-- AI Response -->
        <div v-else-if="advice" class="advice-content">
          <div class="advice-header">
            <div class="gigachat-badge">
              <span class="gc-dot"></span>
              Подсказка от GigaChat
            </div>
          </div>
          <div class="advice-body" v-html="renderedAdvice"></div>
        </div>

        <!-- Initial state - no advice yet -->
        <div v-else class="initial-state">
          <div class="initial-icon">💡</div>
          <p>Нажмите «Получить подсказку», чтобы AI проанализировал задание и дал рекомендации по выполнению.</p>
          <p class="initial-note">AI не даст готовое решение, но поможет разобраться!</p>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="emit('close')">Закрыть</button>
        <button 
          class="btn btn-primary ai-btn" 
          @click="getHelp" 
          :disabled="isLoading"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px">
            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.93V15a1 1 0 0 0-2 0v1.93A8 8 0 0 1 4.07 13H6a1 1 0 0 0 0-2H4.07A8 8 0 0 1 11 4.07V6a1 1 0 0 0 2 0V4.07A8 8 0 0 1 19.93 11H18a1 1 0 0 0 0 2h1.93A8 8 0 0 1 13 16.93z"/>
          </svg>
          {{ isLoading ? 'Загрузка...' : (advice ? 'Обновить подсказку' : 'Получить подсказку') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '@/api/index.js'

const props = defineProps({
  assignment: { type: Object, required: true }
})

const emit = defineEmits(['close'])

const question = ref('')
const advice = ref(props.assignment.ai_advice || '')
const isLoading = ref(false)
const error = ref('')

function statusLabel(status) {
  return { pending: 'Ожидает', progress: 'В процессе', done: 'Сдано', overdue: 'Просрочено' }[status] ?? status
}

async function getHelp() {
  isLoading.value = true
  error.value = ''
  
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
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li><span class="li-num">$1.</span> $2</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/<\/li>\n<li>/g, '</li><li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/<p><\/p>/g, '')
})
</script>

<style scoped>
.ai-help-modal {
  max-width: 600px;
  max-height: 85vh;
}

.ai-icon {
  margin-right: 8px;
}

.assignment-info {
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  padding: 14px;
  margin-bottom: 16px;
}

.assignment-info-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
}

.assignment-info-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.5;
}

.assignment-info-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-muted);
}

.question-section {
  margin-bottom: 16px;
}

.question-input {
  resize: vertical;
  min-height: 60px;
}

.gigachat-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: #1a7a32;
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
  border-radius: 99px;
  padding: 3px 10px;
}

.gc-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #1a7a32;
  display: inline-block;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 40px 20px;
}

.loading-state span {
  font-size: 13px;
  color: var(--text-muted);
}

.error-state {
  text-align: center;
  padding: 30px 20px;
}

.error-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.error-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 6px;
}

.error-msg {
  font-size: 13px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 8px;
  padding: 10px 14px;
}

.initial-state {
  text-align: center;
  padding: 30px 20px;
  color: var(--text-muted);
}

.initial-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.initial-state p {
  font-size: 13.5px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.initial-note {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

.advice-content {
  background: #f0fdf4;
  border: 1px solid #a5d6a7;
  border-radius: var(--radius-sm);
  padding: 16px;
}

.advice-header {
  margin-bottom: 12px;
}

.advice-body {
  line-height: 1.8;
  color: var(--text-secondary);
  font-size: 13.5px;
}

.advice-body :deep(h1) {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  margin: 14px 0 6px;
  color: var(--text-primary);
}

.advice-body :deep(h2) {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  margin: 12px 0 4px;
  color: var(--text-primary);
}

.advice-body :deep(h3) {
  font-size: 14px;
  font-weight: 600;
  margin: 10px 0 4px;
  color: var(--text-primary);
}

.advice-body :deep(strong) {
  font-weight: 600;
  color: var(--text-primary);
}

.advice-body :deep(ul) {
  list-style: none;
  padding-left: 0;
  margin: 8px 0;
}

.advice-body :deep(li) {
  display: flex;
  gap: 8px;
  padding: 3px 0;
}

.advice-body :deep(li)::before {
  content: '—';
  color: var(--text-muted);
  flex-shrink: 0;
}

.advice-body :deep(.li-num) {
  color: var(--accent);
  font-weight: 600;
  flex-shrink: 0;
}

.advice-body :deep(p) {
  margin: 8px 0;
}

.ai-btn {
  background: linear-gradient(135deg, #1a7a32, #0f5522);
}

.ai-btn:hover {
  opacity: 0.9;
}
</style>