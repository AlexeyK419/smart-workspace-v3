<template>
  <section class="card ai-project-card">
    <div class="card-header ai-head">
      <div>
        <div class="card-title">AI-сводка проекта</div>
        <div class="ai-sub">Статусы, дедлайны, нагрузка, риски и координация команды.</div>
      </div>
      <button class="btn btn-ghost ai-refresh" :disabled="isLoading" @click="fetchSummary(true)">
        {{ isLoading ? 'Обновляем…' : 'Обновить' }}
      </button>
    </div>

    <div v-if="isLoading" class="ai-loading">
      <div class="assistant-badge">
        <span class="assistant-dot"></span>
        Ассистент анализирует проект
      </div>
      <div class="dots"><span></span><span></span><span></span></div>
    </div>

    <div v-else-if="error" class="ai-error">
      <div class="error-title">Не удалось получить AI-сводку</div>
      <div class="error-msg">{{ error }}</div>
    </div>

    <div v-else-if="summary" class="ai-content" v-html="renderedSummary"></div>

    <div v-else class="ai-empty">Сводка пока недоступна.</div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
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

const renderedSummary = computed(() => {
  if (!summary.value) return ''
  const escaped = summary.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  return escaped
    .split('\n')
    .map((rawLine) => {
      const line = rawLine.trim()
      if (!line) return '<div class="spacer"></div>'

      const heading = line.match(/^(Состояние проекта|Ближайшие действия команды|Риски|Координация)\s*:?\s*$/)
      if (heading) return `<h3>${heading[1]}</h3>`
      if (line.startsWith('### ')) return `<h3>${line.slice(4)}</h3>`
      if (line.startsWith('## ')) return `<h3>${line.slice(3)}</h3>`

      const numbered = line.match(/^(\d+)\.\s+(.+)$/)
      if (numbered) return `<p class="line-item"><span class="li-num">${numbered[1]}.</span> ${numbered[2]}</p>`
      if (line.startsWith('- ')) return `<p class="line-item">— ${line.slice(2)}</p>`
      return `<p>${line}</p>`
    })
    .join('')
})

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
.ai-head {
  align-items: flex-start;
  gap: 12px;
}
.ai-sub {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}
.ai-refresh {
  flex-shrink: 0;
}
.ai-refresh:disabled {
  opacity: 0.7;
  cursor: wait;
}
.assistant-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-light);
  border: 1px solid var(--accent-mid);
  border-radius: 999px;
  padding: 3px 10px;
}
.assistant-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  display: inline-block;
}
.ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 30px 0 10px;
}
.ai-error {
  border: 1px solid var(--danger-bg);
  background: color-mix(in srgb, var(--danger-bg) 65%, transparent);
  border-radius: var(--radius-sm);
  padding: 12px;
}
.error-title {
  font-weight: 600;
  color: var(--danger);
  margin-bottom: 5px;
}
.error-msg {
  color: var(--text-secondary);
  font-size: 13px;
}
.ai-empty {
  color: var(--text-muted);
}
.ai-content {
  line-height: 1.75;
  font-size: 13px;
  color: var(--text-secondary);
}
.ai-content :deep(h3) {
  margin: 12px 0 6px;
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 700;
}
.ai-content :deep(p) {
  margin: 3px 0;
}
.ai-content :deep(.li-num) {
  color: var(--accent);
  font-weight: 600;
}
.ai-content :deep(.line-item) {
  color: var(--text-secondary);
}
.ai-content :deep(.spacer) {
  height: 4px;
}
</style>
