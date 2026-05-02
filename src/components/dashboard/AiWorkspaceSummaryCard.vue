<template>
  <AiRecommendationCard
    class="ai-workspace-card"
    title="AI-рекомендации workspace"
    description="Краткий срез по дедлайнам, расписанию, проектам и рискам на сегодня."
    variant="workspace"
    :text="summary"
    :loading="isLoading"
    :error="error"
    loading-text="Ассистент анализирует workspace"
    empty-title="Сводка пока недоступна"
    empty-text="Нажмите «Обновить», чтобы сформировать AI-сводку workspace."
  >
    <template #actions>
      <button class="btn btn-ghost ai-refresh" :disabled="isLoading" @click="fetchSummary">
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

const store = useWorkspaceStore()
const isLoading = ref(false)
const error = ref('')
const summary = ref(store.currentUser?.workspace_ai_summary || '')

watch(
  () => store.currentUser?.workspace_ai_summary,
  (value) => {
    summary.value = value || ''
  },
  { immediate: true }
)

async function fetchSummary() {
  isLoading.value = true
  error.value = ''
  try {
    const res = await store.fetchAiWorkspaceSummary()
    summary.value = (res?.summary || '').trim()
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.ai-workspace-card {
  margin-top: 0;
}
.ai-refresh {
  flex-shrink: 0;
}
.ai-refresh:disabled {
  opacity: 0.7;
  cursor: wait;
}
</style>
