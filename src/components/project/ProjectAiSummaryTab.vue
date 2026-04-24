<template>
  <AiRecommendationCard
    class="ai-project-card"
    title="AI-сводка проекта"
    description="Статусы, дедлайны, нагрузка, риски и координация команды."
    variant="project"
    :text="summary"
    :loading="isLoading"
    :error="error"
    loading-text="Ассистент анализирует проект"
    empty-title="Сводка проекта пока недоступна"
    empty-text="Обновите AI-сводку, чтобы увидеть состояние проекта и следующие действия."
  >
    <template #actions>
      <button class="btn btn-ghost ai-refresh" :disabled="isLoading" @click="fetchSummary(true)">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M20 12a8 8 0 0 1-14.9 4M4 12A8 8 0 0 1 18.9 8M19 4v4h-4M5 20v-4h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ isLoading ? 'Обновляем...' : 'Обновить' }}
      </button>
    </template>
  </AiRecommendationCard>
</template>

<script setup>
import { ref, watch } from 'vue'
import AiRecommendationCard from '@/components/ai/AiRecommendationCard.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const props = defineProps({
  projectId: { type: Number, required: true },
})

const store = useWorkspaceStore()
const isLoading = ref(false)
const error = ref('')
const summary = ref('')

async function fetchSummary(force = false) {
  if (!props.projectId) return
  isLoading.value = true
  error.value = ''
  try {
    const res = await store.fetchAiProjectSummary(props.projectId, { force })
    summary.value = (res?.summary || '').trim()
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

watch(
  () => [props.projectId, store.getProjectAiContextKey(props.projectId)],
  () => {
    fetchSummary(false)
  },
  { immediate: true }
)
</script>

<style scoped>
.ai-project-card {
  min-height: 220px;
}
.ai-refresh {
  flex-shrink: 0;
}
.ai-refresh:disabled {
  opacity: 0.7;
  cursor: wait;
}
</style>
