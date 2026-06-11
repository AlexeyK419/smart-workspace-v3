<template>
  <section class="ai-rec-card card" :class="[`ai-rec-${variant}`, { compact }]">
    <div class="ai-rec-header">
      <div class="ai-rec-title-row">
        <div class="ai-rec-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 3l1.7 5.1L19 10l-5.3 1.9L12 17l-1.7-5.1L5 10l5.3-1.9L12 3z" fill="currentColor"/>
            <path d="M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14z" fill="currentColor"/>
          </svg>
        </div>
        <div class="ai-rec-copy">
          <div class="ai-rec-kicker">
            <span class="ai-rec-badge">AI</span>
            <span>{{ eyebrow }}</span>
          </div>
          <h3>{{ title }}</h3>
          <p v-if="description">{{ description }}</p>
        </div>
      </div>

      <div class="ai-rec-actions">
        <slot name="actions"></slot>
      </div>
    </div>

    <div class="ai-rec-chips" v-if="resolvedChips.length">
      <span v-for="chip in resolvedChips" :key="chip.label" class="ai-status-chip" :class="`chip-${chip.tone}`">
        {{ chip.label }}
      </span>
    </div>

    <div v-if="loading" class="ai-state ai-loading">
      <div class="ai-state-pill">
        <span class="assistant-dot"></span>
        {{ loadingText }}
      </div>
      <div class="dots"><span></span><span></span><span></span></div>
    </div>

    <div v-else-if="error" class="ai-state ai-error">
      <div class="ai-state-icon">!</div>
      <div>
        <div class="ai-state-title">Не удалось получить ответ AI</div>
        <div class="ai-state-text">{{ error }}</div>
      </div>
    </div>

    <div v-else-if="text" class="ai-sections">
      <article v-for="section in sections" :key="section.key" class="ai-section">
        <div class="ai-section-head">
          <span class="ai-section-icon" aria-hidden="true">{{ section.icon }}</span>
          <div>
            <div class="ai-section-title">{{ section.title }}</div>
            <div class="ai-section-sub">{{ section.subtitle }}</div>
          </div>
        </div>
        <ul class="ai-section-list">
          <li v-for="(item, index) in section.items" :key="`${section.key}-${index}`">
            <span class="ai-list-marker"></span>
            <span>{{ item }}</span>
          </li>
        </ul>
      </article>
    </div>

    <div v-else class="ai-state ai-empty">
      <div class="ai-state-icon">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M12 4v3m0 10v3m8-8h-3M7 12H4m12.7-4.7-2.1 2.1M9.4 14.6l-2.1 2.1m9.4 0-2.1-2.1M9.4 9.4 7.3 7.3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <div class="ai-state-title">{{ emptyTitle }}</div>
        <div class="ai-state-text">{{ emptyText }}</div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  text: { type: String, default: '' },
  variant: { type: String, default: 'workspace' },
  eyebrow: { type: String, default: 'Smart Assistant' },
  chips: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  loadingText: { type: String, default: 'Ассистент анализирует контекст' },
  emptyTitle: { type: String, default: 'AI-рекомендации пока не готовы' },
  emptyText: { type: String, default: 'Запустите генерацию, чтобы получить краткий план действий.' },
  compact: { type: Boolean, default: false },
})

const SECTION_META = {
  focus: { title: 'Фокус', icon: '◎', subtitle: 'Главное, на что стоит обратить внимание' },
  now: { title: 'Что сделать сейчас', icon: '✓', subtitle: 'Ближайшие практические действия' },
  risks: { title: 'Риски', icon: '!', subtitle: 'Что может помешать и где нужен контроль' },
  advice: { title: 'Совет ИИ', icon: 'AI', subtitle: 'Короткая рекомендация ассистента' },
  next: { title: 'Следующие шаги', icon: '→', subtitle: 'Порядок дальнейшей работы' },
}

const HEADING_ALIASES = new Map([
  ['фокус', 'focus'],
  ['состояние проекта', 'focus'],
  ['что означает задание', 'focus'],
  ['цель', 'focus'],
  ['приоритеты', 'focus'],
  ['что сделать сейчас', 'now'],
  ['с чего начать', 'now'],
  ['ближайшие действия', 'now'],
  ['ближайшие действия команды', 'now'],
  ['этапы', 'next'],
  ['шаги', 'next'],
  ['следующие шаги', 'next'],
  ['план', 'next'],
  ['риски', 'risks'],
  ['на что обратить внимание', 'risks'],
  ['совет', 'advice'],
  ['совет ии', 'advice'],
  ['советы', 'advice'],
  ['советы по темпу', 'advice'],
  ['координация', 'advice'],
])

const DEFAULT_CHIPS = {
  workspace: [
    { label: 'Высокий приоритет', tone: 'priority' },
    { label: 'Сегодня', tone: 'today' },
    { label: 'AI', tone: 'ai' },
  ],
  course: [
    { label: 'По курсу', tone: 'course' },
    { label: 'Следующие шаги', tone: 'today' },
    { label: 'AI', tone: 'ai' },
  ],
  assignment: [
    { label: 'Высокий приоритет', tone: 'priority' },
    { label: 'Сегодня', tone: 'today' },
    { label: 'AI', tone: 'ai' },
  ],
  project: [
    { label: 'Проект', tone: 'project' },
    { label: 'Риски', tone: 'priority' },
    { label: 'AI', tone: 'ai' },
  ],
}

const resolvedChips = computed(() => props.chips.length ? props.chips : (DEFAULT_CHIPS[props.variant] || DEFAULT_CHIPS.workspace))

const sections = computed(() => parseAiText(props.text))

function parseAiText(rawText) {
  const lines = rawText
    .split('\n')
    .map((line) => line.trim())

  const parsed = []
  let current = null

  for (const rawLine of lines) {
    if (!rawLine) continue

    const heading = resolveHeading(rawLine)
    if (heading) {
      current = createSection(heading.key, heading.title)
      parsed.push(current)
      continue
    }

    if (!current) {
      current = createSection('focus')
      parsed.push(current)
    }

    const cleaned = cleanLine(rawLine)
    if (cleaned) current.items.push(cleaned)
  }

  return parsed
    .filter((section) => section.items.length)
    .map((section, index) => ({ ...section, key: `${section.key}-${index}` }))
}

function resolveHeading(line) {
  const normalized = line
    .replace(/^#{1,6}\s*/, '')
    .replace(/^\*\*(.+)\*\*$/, '$1')
    .replace(/:$/, '')
    .trim()

  const key = HEADING_ALIASES.get(normalized.toLowerCase())
  if (key) return { key }

  if (normalized.length <= 42 && !/[.!?]$/.test(normalized) && (line === normalized || /^#{1,6}\s/.test(line))) {
    return { key: 'next', title: normalized }
  }

  return null
}

function createSection(key, customTitle = '') {
  const meta = SECTION_META[key] || SECTION_META.next
  return {
    key,
    title: customTitle || meta.title,
    icon: meta.icon,
    subtitle: meta.subtitle,
    items: [],
  }
}

function cleanLine(line) {
  return line
    .replace(/^[-*•]\s*/, '')
    .replace(/^\d+[.)]\s*/, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .trim()
}
</script>

<style scoped>
.ai-rec-card {
  position: relative;
  overflow: hidden;
  border-color: color-mix(in srgb, var(--accent-mid) 56%, var(--border));
  box-shadow: 0 18px 45px rgba(31, 26, 20, 0.08), 0 4px 14px rgba(53, 89, 216, 0.08);
}



.ai-rec-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.ai-rec-title-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.ai-rec-icon {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: var(--accent);
  background: linear-gradient(145deg, var(--accent-light), color-mix(in srgb, var(--surface) 88%, transparent));
  border: 1px solid var(--accent-mid);
  box-shadow: 0 10px 20px color-mix(in srgb, var(--accent) 12%, transparent);
}

.ai-rec-icon svg {
  width: 20px;
  height: 20px;
}

.ai-rec-kicker {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 3px;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.ai-rec-badge,
.ai-status-chip,
.ai-state-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  white-space: nowrap;
}

.ai-rec-badge {
  padding: 2px 7px;
  color: var(--accent);
  background: var(--accent-light);
  border: 1px solid var(--accent-mid);
}

.ai-rec-copy h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 19px;
  line-height: 1.2;
  font-weight: 600;
}

.ai-rec-copy p {
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.45;
}

.ai-rec-actions {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.ai-rec-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 16px;
}

.ai-status-chip {
  min-height: 24px;
  padding: 4px 9px;
  font-size: 11.5px;
  font-weight: 700;
  border: 1px solid transparent;
}

.chip-priority { color: var(--danger); background: var(--danger-bg); border-color: color-mix(in srgb, var(--danger) 22%, transparent); }
.chip-today { color: var(--warning); background: var(--warning-bg); border-color: color-mix(in srgb, var(--warning) 22%, transparent); }
.chip-course { color: var(--accent); background: var(--accent-light); border-color: var(--accent-mid); }
.chip-project { color: var(--success); background: var(--success-bg); border-color: color-mix(in srgb, var(--success) 22%, transparent); }
.chip-ai { color: var(--text-primary); background: color-mix(in srgb, var(--surface-2) 78%, transparent); border-color: var(--border-soft); }

.ai-sections {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.ai-section {
  background: color-mix(in srgb, var(--surface) 86%, transparent);
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 8px 22px rgba(31, 26, 20, 0.04);
}

.ai-section:first-child {
  grid-column: 1 / -1;
}

.ai-section-head {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding-bottom: 10px;
  margin-bottom: 9px;
  border-bottom: 1px solid var(--border-soft);
}

.ai-section-icon {
  width: 26px;
  height: 26px;
  flex: 0 0 26px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: var(--accent);
  background: var(--accent-light);
  font-size: 11px;
  font-weight: 800;
}

.ai-section-title {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 800;
}

.ai-section-sub {
  margin-top: 1px;
  color: var(--text-muted);
  font-size: 11.5px;
  line-height: 1.35;
}

.ai-section-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  list-style: none;
}

.ai-section-list li {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.ai-list-marker {
  width: 6px;
  height: 6px;
  margin-top: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-light);
}

.ai-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 150px;
  padding: 22px;
  border: 1px dashed var(--border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface-2) 48%, transparent);
}

.ai-loading {
  flex-direction: column;
}

.ai-state-pill {
  gap: 7px;
  padding: 5px 11px;
  color: var(--accent);
  background: var(--accent-light);
  border: 1px solid var(--accent-mid);
  font-size: 12px;
  font-weight: 700;
}

.assistant-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
}

.ai-error {
  justify-content: flex-start;
  border-style: solid;
  border-color: color-mix(in srgb, var(--danger) 30%, var(--border));
  background: color-mix(in srgb, var(--danger-bg) 72%, transparent);
}

.ai-empty {
  justify-content: flex-start;
}

.ai-state-icon {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: var(--accent);
  background: var(--accent-light);
  font-weight: 800;
}

.ai-error .ai-state-icon {
  color: var(--danger);
  background: var(--danger-bg);
}

.ai-state-icon svg {
  width: 18px;
  height: 18px;
}

.ai-state-title {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 800;
}

.ai-state-text {
  margin-top: 3px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.45;
}

.compact .ai-sections {
  grid-template-columns: 1fr;
}

.compact .ai-section:first-child {
  grid-column: auto;
}

@media (max-width: 760px) {
  .ai-rec-header {
    flex-direction: column;
  }

  .ai-rec-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .ai-sections {
    grid-template-columns: 1fr;
  }

  .ai-section:first-child {
    grid-column: auto;
  }
}
</style>
