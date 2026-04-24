<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal ai-help-modal">
      <div class="modal-header">
        <div class="modal-title">
          <span class="ai-icon">✨</span>
          AI-помощник по заданию
        </div>
        <button class="modal-close" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="assignment-info">
          <div class="assignment-info-title">{{ assignment.title }}</div>
          <div class="assignment-info-desc" v-if="assignment.description">{{ assignment.description }}</div>
          <div class="assignment-info-meta">
            <span v-if="assignment.deadline">📅 {{ assignment.deadline }}</span>
            <span class="chip" :class="'chip-' + assignment.status">{{ statusLabel(assignment.status) }}</span>
          </div>
        </div>

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

        <AiRecommendationCard
          v-if="isLoading || error || advice"
          title="AI-помощь к заданию"
          description="Разбор смысла задания, стартовый фокус, риски и следующий безопасный шаг."
          variant="assignment"
          :text="advice"
          :loading="isLoading"
          :error="error"
          loading-text="Ассистент анализирует задание и готовит подсказки"
          empty-title="Подсказка пока не готова"
          empty-text="Задайте вопрос или запросите помощь, чтобы получить структурированную рекомендацию."
          compact
        >
          <template #actions>
            <button v-if="error" class="btn btn-ghost compact-action" @click="error = ''">Попробовать снова</button>
          </template>
        </AiRecommendationCard>

        <div v-else class="initial-state">
          <div class="initial-icon">💡</div>
          <p>Нажмите «Получить подсказку», чтобы ассистент помог разобрать задание и предложил следующий шаг.</p>
          <p class="initial-note">Готовое решение он не даст, но поможет понять, как действовать дальше.</p>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="emit('close')">Закрыть</button>
        <button class="btn btn-primary ai-btn" @click="getHelp" :disabled="isLoading">
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
import { ref } from 'vue'
import AiRecommendationCard from '@/components/ai/AiRecommendationCard.vue'
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
.initial-state {
  text-align: center;
  padding: 30px 20px;
  color: var(--text-muted);
}
.initial-icon {
  font-size: 36px;
  margin-bottom: 12px;
}
.initial-note {
  margin-top: 6px;
}
.ai-btn svg {
  margin-right: 2px;
}
.compact-action {
  padding: 7px 11px;
  font-size: 12px;
}
</style>
