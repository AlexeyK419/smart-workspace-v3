<template>
  <div class="ai-plan-wrap card">
    <div class="ai-plan-header">
      <div>
        <div class="ai-plan-title">ИИ-учебный план</div>
        <div class="ai-plan-sub">Персональный план обучения на основе материалов и заданий курса</div>
      </div>
      <button class="gen-btn" :class="{ loading: isLoading }" @click="generate" :disabled="isLoading">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.93V15a1 1 0 0 0-2 0v1.93A8 8 0 0 1 4.07 11H6a1 1 0 0 0 0-2H4.07A8 8 0 0 1 11 4.07V6a1 1 0 0 0 2 0V4.07A8 8 0 0 1 19.93 11H18a1 1 0 0 0 0 2h1.93A8 8 0 0 1 13 16.93z"/></svg>
        {{ isLoading ? 'Ассистент думает...' : (planText ? 'Пересоздать план' : 'Сгенерировать план') }}
      </button>
    </div>

    <div v-if="!isLoading && !planText" class="context-wrap">
      <label class="form-label">Ваши пожелания (необязательно)</label>
      <textarea class="form-input context-input" v-model="extraContext" rows="2"
        placeholder="Например: хочу сдать экзамен на отлично, основная сложность — теоремы..."></textarea>
    </div>

    <AiRecommendationCard
      v-if="isLoading || error || planText"
      title="AI-план по курсу"
      description="Персональный маршрут обучения на основе материалов, заданий и ваших пожеланий."
      variant="course"
      :text="planText"
      :loading="isLoading"
      :error="error"
      loading-text="Ассистент анализирует курс и составляет план"
      empty-title="План пока не создан"
      empty-text="Сгенерируйте AI-план, чтобы получить фокус, риски и следующие шаги по курсу."
    >
      <template #actions>
        <button v-if="planText" class="btn btn-ghost compact-action" @click="regenerate">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M20 12a8 8 0 0 1-14.9 4M4 12A8 8 0 0 1 18.9 8M19 4v4h-4M5 20v-4h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Пересоздать
        </button>
        <button v-else-if="error" class="btn btn-ghost compact-action" @click="error = ''">Попробовать снова</button>
      </template>
    </AiRecommendationCard>

    <div v-else class="empty-state">
      <div class="empty-icon">🎯</div>
      <p>Нажмите «Сгенерировать план» — ассистент соберёт<br/>для вас понятный маршрут обучения по курсу</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import AiRecommendationCard from '@/components/ai/AiRecommendationCard.vue'
import { api } from '@/api/index.js'

const props = defineProps({
  courseId:  { type: Number, required: true },
  savedPlan: { type: String, default: '' },
})

const isLoading = ref(false)
const planText = ref('')
const extraContext = ref('')
const error = ref('')

onMounted(() => {
  if (props.savedPlan) planText.value = props.savedPlan
})

watch(() => props.courseId, () => {
  planText.value = props.savedPlan || ''
  extraContext.value = ''
  error.value = ''
})

watch(() => props.savedPlan, (value) => {
  if (value && !planText.value) planText.value = value
})

async function generate() {
  isLoading.value = true
  planText.value = ''
  error.value = ''
  try {
    const res = await api.aiGeneratePlan(props.courseId, extraContext.value)
    planText.value = res.plan
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

function regenerate() {
  planText.value = ''
  generate()
}

</script>

<style scoped>
.ai-plan-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}
.ai-plan-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
}
.ai-plan-sub {
  font-size: 12.5px;
  color: var(--text-muted);
  margin-top: 3px;
}
.gen-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 18px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--accent);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: var(--font-body);
}
.gen-btn:hover {
  background: #2e42c4;
}
.gen-btn.loading {
  opacity: 0.7;
  cursor: wait;
}
.gen-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
.context-wrap {
  margin-bottom: 16px;
}
.context-input {
  resize: vertical;
  min-height: 60px;
}
.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 40px;
  margin-bottom: 12px;
}
.compact-action {
  padding: 7px 11px;
  font-size: 12px;
}

@media (max-width: 680px) {
  .ai-plan-header {
    flex-direction: column;
  }

  .gen-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
