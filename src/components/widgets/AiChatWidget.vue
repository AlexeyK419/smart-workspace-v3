<template>
  <Transition name="chat-slide">
    <div v-if="isOpen" class="chat-panel">
      <div class="chat-panel-header">
        <div class="assistant-avatar">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm4.59 12.59L15.17 16 12 12.83 8.83 16l-1.42-1.41L10.59 11 7.41 7.83l1.42-1.42L12 9.59l3.17-3.18 1.42 1.42L13.41 11z"/></svg>
        </div>
        <div class="chat-ai-info">
          <div class="chat-ai-name">Ассистент Workspace</div>
          <div class="chat-ai-status" :class="{ error: apiError }">
            {{ apiError ? 'Временно недоступен' : 'Онлайн и готов помочь' }}
          </div>
        </div>
        <button class="chat-close-btn" @click="isOpen = false">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="chat-messages" ref="messagesEl">
        <div v-for="msg in messages" :key="msg.id" class="msg" :class="msg.role">
          <div class="msg-avatar" :class="msg.role === 'assistant' ? 'ai-av' : 'user-av'">
            {{ msg.role === 'assistant' ? 'AI' : 'Вы' }}
          </div>
          <div>
            <div class="msg-bubble" v-html="renderMd(msg.content)"></div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>

        <div v-if="isTyping" class="msg assistant">
          <div class="msg-avatar ai-av">AI</div>
          <div class="typing-bubble">
            <div class="dots"><span></span><span></span><span></span></div>
          </div>
        </div>

        <div v-if="apiError && !isTyping" class="error-bubble">
          ⚠️ {{ apiError }}
          <span class="error-hint">Проверь настройки AI-сервиса на сервере.</span>
        </div>
      </div>

      <div v-if="suggestions.length" class="chat-suggestions">
        <button v-for="suggestion in suggestions" :key="suggestion" class="suggestion-chip" @click="sendText(suggestion)">
          {{ suggestion }}
        </button>
      </div>

      <div class="chat-input-wrap">
        <textarea
          ref="inputEl"
          class="chat-input"
          v-model="inputText"
          placeholder="Спроси ассистента о курсе, дедлайне или теме..."
          rows="1"
          :disabled="isTyping"
          @keydown.enter.exact.prevent="send"
        ></textarea>
        <button class="chat-send-btn" @click="send" :disabled="isTyping || !inputText.trim()">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>
  </Transition>

  <button class="chat-fab" @click="isOpen = !isOpen">
    <Transition name="icon-swap" mode="out-in">
      <svg v-if="!isOpen" key="chat" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
      </svg>
      <svg v-else key="close" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
      </svg>
    </Transition>
  </button>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { api } from '@/api/index.js'

const isOpen = ref(false)
const isTyping = ref(false)
const inputText = ref('')
const apiError = ref('')
const messagesEl = ref(null)

const history = ref([])
const messages = ref([
  {
    id: 1,
    role: 'assistant',
    time: now(),
    content: 'Привет! Я **ассистент Workspace**. Помогу разобрать тему, составить план подготовки и подсказать следующий шаг по заданию. Готовые решения не даю, но могу помочь дойти до них самому.',
  },
])

const suggestions = ref([
  'Объясни красно-чёрные деревья',
  'Как подступиться к лабораторной по БД?',
  'Помоги спланировать подготовку к дедлайну',
])

function now() {
  return new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

async function send() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  apiError.value = ''
  suggestions.value = []
  inputText.value = ''

  messages.value.push({ id: Date.now(), role: 'user', content: text, time: now() })
  history.value.push({ role: 'user', content: text })

  await scrollToBottom()
  isTyping.value = true

  try {
    const res = await api.aiChat(history.value)
    const reply = res.reply
    messages.value.push({ id: Date.now() + 1, role: 'assistant', content: reply, time: now() })
    history.value.push({ role: 'assistant', content: reply })
  } catch (e) {
    apiError.value = e.message
  } finally {
    isTyping.value = false
    await scrollToBottom()
  }
}

function sendText(text) {
  inputText.value = text
  send()
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

function renderMd(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}
</script>

<style scoped>
.chat-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 90;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--chat-fab-bg);
  color: var(--chat-fab-fg);
  border: 1px solid var(--chat-fab-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-lg);
  transition: transform var(--transition), box-shadow var(--transition);
}
.chat-fab:hover {
  transform: translateY(-2px);
}
.chat-fab svg {
  width: 22px;
  height: 22px;
}
.chat-panel {
  position: fixed;
  right: 24px;
  bottom: 92px;
  z-index: 90;
  width: 360px;
  height: 560px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}
.chat-panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--chat-header-bg);
}
.assistant-avatar,
.msg-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.assistant-avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: var(--accent-light);
  color: var(--accent);
}
.assistant-avatar svg {
  width: 18px;
  height: 18px;
}
.chat-ai-name {
  font-size: 14px;
  font-weight: 700;
}
.chat-ai-status {
  font-size: 11px;
  color: var(--success);
}
.chat-ai-status.error {
  color: var(--danger);
}
.chat-close-btn {
  margin-left: auto;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chat-close-btn:hover {
  background: var(--surface-2);
}
.chat-close-btn svg {
  width: 14px;
  height: 14px;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.msg {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.msg.user {
  flex-direction: row-reverse;
}
.msg-bubble {
  max-width: 82%;
  padding: 11px 13px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.6;
}
.msg.assistant .msg-bubble {
  background: var(--surface-2);
  border-bottom-left-radius: 6px;
}
.msg.user .msg-bubble {
  background: var(--accent);
  color: white;
  border-bottom-right-radius: 6px;
}
.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
}
.ai-av {
  background: var(--accent-light);
  color: var(--accent);
}
.user-av {
  background: var(--text-primary);
  color: white;
}
.msg-time {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 3px;
  text-align: right;
}
.typing-bubble {
  background: var(--surface-2);
  border-radius: 16px;
  border-bottom-left-radius: 6px;
  padding: 12px 16px;
}
.error-bubble {
  background: var(--danger-bg);
  color: var(--danger);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 12.5px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.error-hint {
  font-size: 11px;
  color: var(--text-muted);
}
.chat-suggestions {
  padding: 0 14px 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.suggestion-chip {
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-2);
  cursor: pointer;
  color: var(--text-secondary);
  font-family: var(--font-body);
}
.suggestion-chip:hover {
  background: var(--accent-light);
  color: var(--accent);
  border-color: var(--accent-mid);
}
.chat-input-wrap {
  padding: 12px 14px;
  border-top: 1px solid var(--border-soft);
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.chat-input {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 10px 12px;
  font-size: 13px;
  resize: none;
  outline: none;
  font-family: var(--font-body);
  background: var(--bg);
  max-height: 84px;
  line-height: 1.5;
}
.chat-input:focus {
  border-color: var(--accent);
  background: var(--surface);
}
.chat-send-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  flex-shrink: 0;
  background: var(--accent);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chat-send-btn:hover {
  background: #2e42c4;
}
.chat-send-btn svg {
  width: 16px;
  height: 16px;
}
.chat-send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.98);
}
.icon-swap-enter-active,
.icon-swap-leave-active {
  transition: all 0.15s ease;
}
.icon-swap-enter-from,
.icon-swap-leave-to {
  opacity: 0;
  transform: scale(0.7) rotate(25deg);
}
</style>
