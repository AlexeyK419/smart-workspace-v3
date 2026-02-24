<template>
  <div class="ai-plan-wrap card">
    <div class="ai-plan-header">
      <div>
        <div class="ai-plan-title">ИИ-Учебный план</div>
        <div class="ai-plan-sub">Персонализированный план от GigaChat на основе всех материалов и заданий курса</div>
      </div>
      <button class="gen-btn" :class="{ loading: isLoading }" @click="generate" :disabled="isLoading">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.93V15a1 1 0 0 0-2 0v1.93A8 8 0 0 1 4.07 11H6a1 1 0 0 0 0-2H4.07A8 8 0 0 1 11 4.07V6a1 1 0 0 0 2 0V4.07A8 8 0 0 1 19.93 11H18a1 1 0 0 0 0 2h1.93A8 8 0 0 1 13 16.93z"/></svg>
        {{ isLoading ? 'GigaChat думает...' : (planText ? 'Пересоздать план' : 'Сгенерировать план') }}
      </button>
    </div>

    <!-- Extra context input -->
    <div v-if="!isLoading && !planText" class="context-wrap">
      <label class="form-label">Ваши пожелания (необязательно)</label>
      <textarea class="form-input context-input" v-model="extraContext" rows="2"
        placeholder="Например: хочу сдать экзамен на отлично, основная сложность — теоремы..."></textarea>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="loading-state">
      <div class="gigachat-badge">
        <span class="gc-dot"></span>
        GigaChat
      </div>
      <div class="dots"><span></span><span></span><span></span></div>
      <span>Анализирует курс и составляет план...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <div class="error-title">Ошибка GigaChat</div>
      <div class="error-msg">{{ error }}</div>
      <button class="btn btn-ghost" style="margin-top:12px" @click="error = ''">Попробовать снова</button>
    </div>

    <!-- Plan (rendered markdown-like) -->
    <div v-else-if="planText" class="plan-content">
      <div class="plan-toolbar">
        <div class="gigachat-badge">
          <span class="gc-dot"></span>
          Сгенерировано GigaChat
        </div>
        <button class="btn btn-ghost" style="padding:5px 10px;font-size:12px" @click="regenerate">
          ↺ Пересоздать
        </button>
      </div>
      <div class="plan-body" v-html="renderedPlan"></div>
    </div>

    <!-- Empty -->
    <div v-else class="empty-state">
      <div class="empty-icon">🎯</div>
      <p>Нажмите «Сгенерировать план» — GigaChat составит<br/>персонализированный учебный план для этого курса</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '@/api/index.js'

const props = defineProps({
  courseId:  { type: Number, required: true },
  savedPlan: { type: String, default: '' },
})

const isLoading    = ref(false)
const planText     = ref('')
const extraContext = ref('')
const error        = ref('')

onMounted(() => {
  if (props.savedPlan) {
    planText.value = props.savedPlan
  }
})

watch(() => props.courseId, () => {
  planText.value   = props.savedPlan || ''
  extraContext.value = ''
  error.value      = ''
})

watch(() => props.savedPlan, (v) => {
  if (v && !planText.value) planText.value = v
})

async function generate() {
  isLoading.value = true
  planText.value  = ''
  error.value     = ''
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

const renderedPlan = computed(() => {
  if (!planText.value) return ''
  return planText.value
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/^- (.+)$/gm,    '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li><span class="li-num">$1.</span> $2</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hli])(.+)$/gm, (m) => m ? m : '')
    .replace(/<\/li>\n<li>/g, '</li><li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/<p><\/p>/g, '')
})
</script>

<style scoped>
.ai-plan-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 12px; margin-bottom: 18px;
}
.ai-plan-title { font-family: var(--font-display); font-size: 18px; font-weight: 600; }
.ai-plan-sub   { font-size: 12.5px; color: var(--text-muted); margin-top: 3px; }
.gen-btn {
  display: flex; align-items: center; gap: 8px; padding: 9px 18px;
  border-radius: var(--radius-sm); border: none;
  background: linear-gradient(135deg, #1a7a32, #0f5522);
  color: white; font-size: 13px; font-weight: 500; cursor: pointer;
  transition: opacity var(--transition), transform var(--transition);
  font-family: var(--font-body); white-space: nowrap; flex-shrink: 0;
}
.gen-btn:hover { opacity: .9; }
.gen-btn:active { transform: scale(.97); }
.gen-btn.loading { opacity: .7; cursor: wait; }
.gen-btn svg { width: 15px; height: 15px; }
.context-wrap { margin-bottom: 16px; }
.context-input { resize: vertical; min-height: 60px; }
.gigachat-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11.5px; font-weight: 600; color: #1a7a32;
  background: #e8f5e9; border: 1px solid #a5d6a7;
  border-radius: 99px; padding: 3px 10px;
}
.gc-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #1a7a32; display: inline-block;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  gap: 14px; padding: 48px 20px;
}
.loading-state span { font-size: 13px; color: var(--text-muted); }
.error-state { text-align: center; padding: 40px 20px; }
.error-icon  { font-size: 36px; margin-bottom: 10px; }
.error-title { font-weight: 600; font-size: 15px; margin-bottom: 6px; }
.error-msg   { font-size: 13px; color: var(--danger); background: var(--danger-bg); border-radius: 8px; padding: 10px 14px; }
.empty-state { text-align: center; padding: 48px 20px; color: var(--text-muted); }
.empty-icon  { font-size: 40px; margin-bottom: 12px; }
.empty-state p { font-size: 13.5px; line-height: 1.6; }
.plan-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.plan-body { line-height: 1.8; color: var(--text-secondary); font-size: 13.5px; }
.plan-body :deep(h1) { font-family: var(--font-display); font-size: 20px; font-weight: 700; margin: 18px 0 8px; color: var(--text-primary); }
.plan-body :deep(h2) { font-family: var(--font-display); font-size: 16px; font-weight: 600; margin: 14px 0 6px; color: var(--text-primary); }
.plan-body :deep(h3) { font-size: 14px; font-weight: 600; margin: 10px 0 4px; color: var(--text-primary); }
.plan-body :deep(strong) { font-weight: 600; color: var(--text-primary); }
.plan-body :deep(ul)  { list-style: none; padding-left: 0; margin: 8px 0; }
.plan-body :deep(li)  { display: flex; gap: 8px; padding: 3px 0; }
.plan-body :deep(li)::before { content: '—'; color: var(--text-muted); flex-shrink: 0; }
.plan-body :deep(.li-num) { color: var(--accent); font-weight: 600; flex-shrink: 0; }
.plan-body :deep(p)   { margin: 8px 0; }
</style>