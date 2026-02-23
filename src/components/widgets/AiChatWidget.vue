<template>
  <!-- Chat Panel -->
  <Transition name="chat-slide">
    <div v-if="isOpen" class="chat-panel">
      <div class="chat-panel-header">
        <div class="gc-avatar">
          <svg viewBox="0 0 24 24" fill="white" style="width:15px;height:15px"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.93V15a1 1 0 0 0-2 0v1.93A8 8 0 0 1 4.07 11H6a1 1 0 0 0 0-2H4.07A8 8 0 0 1 11 4.07V6a1 1 0 0 0 2 0V4.07A8 8 0 0 1 19.93 11H18a1 1 0 0 0 0 2h1.93A8 8 0 0 1 13 16.93z"/></svg>
        </div>
        <div class="chat-ai-info">
          <div class="chat-ai-name">GigaChat</div>
          <div class="chat-ai-status" :class="{ error: apiError }">
            {{ apiError ? 'Нет соединения' : 'Sberbank AI · Онлайн' }}
          </div>
        </div>
        <button class="chat-close-btn" @click="isOpen = false">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:12px;height:12px"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <!-- Messages -->
      <div class="chat-messages" ref="messagesEl">
        <div v-for="msg in messages" :key="msg.id" class="msg" :class="msg.role">
          <div class="msg-avatar" :class="msg.role === 'assistant' ? 'ai-av' : 'user-av'">
            {{ msg.role === 'assistant' ? '🤖' : 'А' }}
          </div>
          <div>
            <div class="msg-bubble" v-html="renderMd(msg.content)"></div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>

        <!-- Typing indicator -->
        <div v-if="isTyping" class="msg assistant">
          <div class="msg-avatar ai-av">🤖</div>
          <div class="typing-bubble">
            <div class="dots"><span></span><span></span><span></span></div>
          </div>
        </div>

        <!-- Error bubble -->
        <div v-if="apiError && !isTyping" class="error-bubble">
          ⚠️ {{ apiError }}
          <span class="error-hint">Проверьте GIGACHAT_CLIENT_ID в backend/.env</span>
        </div>
      </div>

      <!-- Suggestions (shown only at start) -->
      <div v-if="suggestions.length" class="chat-suggestions">
        <button v-for="s in suggestions" :key="s" class="suggestion-chip" @click="sendText(s)">
          {{ s }}
        </button>
      </div>

      <!-- Input -->
      <div class="chat-input-wrap">
        <textarea
          ref="inputEl"
          class="chat-input"
          v-model="inputText"
          placeholder="Спросите GigaChat..."
          rows="1"
          :disabled="isTyping"
          @keydown.enter.exact.prevent="send"
        ></textarea>
        <button class="chat-send-btn" @click="send" :disabled="isTyping || !inputText.trim()">
          <svg viewBox="0 0 24 24" fill="white" style="width:16px;height:16px"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>
  </Transition>

  <!-- FAB -->
  <button class="chat-fab" @click="isOpen = !isOpen">
    <Transition name="icon-swap" mode="out-in">
      <svg v-if="!isOpen" key="chat" viewBox="0 0 24 24" fill="white" style="width:22px;height:22px">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
      </svg>
      <svg v-else key="close" viewBox="0 0 24 24" fill="white" style="width:22px;height:22px">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
      </svg>
    </Transition>
    <div v-if="!isOpen" class="chat-badge">GC</div>
  </button>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { api } from '@/api/index.js'

const isOpen    = ref(false)
const isTyping  = ref(false)
const inputText = ref('')
const apiError  = ref('')
const messagesEl = ref(null)

// Conversation history sent to GigaChat (role + content only)
const history = ref([])

// Display messages (include id + time for UI)
const messages = ref([
  {
    id: 1, role: 'assistant', time: now(),
    content: 'Привет! Я **GigaChat** — AI-ассистент от Сбера. Помогу разобраться с учебным материалом, составить план подготовки или объяснить сложную тему. Чем могу помочь?',
  },
])

const suggestions = ref([
  'Объясни красно-чёрные деревья',
  'Что такое нормализация БД?',
  'Помоги с планом написания эссе',
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

  // Add user message to display + history
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

// Minimal markdown → HTML for chat bubbles
function renderMd(text) {
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`(.+?)`/g,'<code>$1</code>')
    .replace(/\n/g,'<br/>')
}
</script>

<style scoped>
/* FAB */
.chat-fab {
  position: fixed; right: 24px; bottom: 24px; z-index: 90;
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, #1a7a32, #0f5522);
  border: none; display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 4px 16px rgba(26,122,50,.45);
  transition: transform var(--transition), box-shadow var(--transition);
}
.chat-fab:hover { transform: scale(1.08); box-shadow: 0 6px 24px rgba(26,122,50,.55); }

.chat-badge {
  position: absolute; top: -2px; right: -4px;
  background: #fff; color: #1a7a32; border: 1.5px solid #1a7a32;
  border-radius: 99px; font-size: 9px; font-weight: 800;
  padding: 1px 5px; letter-spacing: 0.3px;
}

/* Panel */
.chat-panel {
  position: fixed; right: 24px; bottom: 84px; z-index: 90;
  width: 350px; height: 520px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 18px; display: flex; flex-direction: column;
  box-shadow: var(--shadow-lg); overflow: hidden;
}

.chat-panel-header {
  padding: 14px 16px; border-bottom: 1px solid var(--border-soft);
  display: flex; align-items: center; gap: 10px;
  background: linear-gradient(to right, #f0fdf4, var(--surface));
}

.gc-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, #1a7a32, #0f5522);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

.chat-ai-name  { font-size: 13.5px; font-weight: 700; color: #1a7a32; }
.chat-ai-status {
  font-size: 11px; color: #2d7a4f;
  display: flex; align-items: center; gap: 4px;
}
.chat-ai-status::before {
  content: ''; width: 6px; height: 6px;
  border-radius: 50%; background: #2d7a4f;
  animation: pulse 2s infinite;
}
.chat-ai-status.error { color: var(--danger); }
.chat-ai-status.error::before { background: var(--danger); animation: none; }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

.chat-close-btn {
  margin-left: auto; width: 26px; height: 26px; border-radius: 6px;
  border: 1px solid var(--border); background: transparent;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.chat-close-btn:hover { background: var(--surface-2); }

/* Messages */
.chat-messages {
  flex: 1; overflow-y: auto; padding: 14px;
  display: flex; flex-direction: column; gap: 10px;
}

.msg { display: flex; gap: 8px; align-items: flex-end; }
.msg.user { flex-direction: row-reverse; }

.msg-bubble {
  max-width: 80%; padding: 9px 13px; border-radius: 14px;
  font-size: 13px; line-height: 1.6;
}
.msg.assistant .msg-bubble {
  background: var(--surface-2); border-bottom-left-radius: 4px;
}
.msg.user .msg-bubble {
  background: linear-gradient(135deg, #1a7a32, #0f5522);
  color: white; border-bottom-right-radius: 4px;
}
.msg.assistant .msg-bubble :deep(code) {
  background: var(--border-soft); border-radius: 4px; padding: 1px 5px;
  font-size: 12px; font-family: 'Courier New', monospace;
}

.msg-avatar {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 11px;
}
.ai-av   { background: linear-gradient(135deg, #1a7a32, #0f5522); color: white; }
.user-av { background: var(--surface-2); color: var(--text-muted); }

.msg-time { font-size: 10px; color: var(--text-muted); margin-top: 2px; text-align: right; }

.typing-bubble {
  background: var(--surface-2); border-radius: 14px;
  border-bottom-left-radius: 4px; padding: 12px 16px;
}

.error-bubble {
  background: var(--danger-bg); color: var(--danger);
  border-radius: 10px; padding: 10px 14px; font-size: 12.5px;
  display: flex; flex-direction: column; gap: 4px;
}
.error-hint { font-size: 11px; color: var(--text-muted); }

/* Suggestions */
.chat-suggestions {
  padding: 0 12px 10px; display: flex; gap: 6px; flex-wrap: wrap;
}
.suggestion-chip {
  font-size: 11px; padding: 4px 10px; border-radius: 99px;
  border: 1px solid #a5d6a7; background: #e8f5e9;
  cursor: pointer; color: #1a7a32; transition: all var(--transition);
  font-family: var(--font-body); white-space: nowrap;
}
.suggestion-chip:hover { background: #1a7a32; color: white; }

/* Input */
.chat-input-wrap {
  padding: 10px 12px; border-top: 1px solid var(--border-soft);
  display: flex; gap: 8px; align-items: flex-end;
}
.chat-input {
  flex: 1; border: 1px solid var(--border); border-radius: 10px;
  padding: 8px 12px; font-size: 13px; resize: none; outline: none;
  font-family: var(--font-body); background: var(--bg);
  max-height: 80px; line-height: 1.5; transition: border-color var(--transition);
}
.chat-input:focus { border-color: #1a7a32; }
.chat-input:disabled { opacity: .6; }

.chat-send-btn {
  width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0;
  background: linear-gradient(135deg, #1a7a32, #0f5522);
  border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: opacity var(--transition), transform var(--transition);
}
.chat-send-btn:hover  { opacity: .9; }
.chat-send-btn:active { transform: scale(.92); }
.chat-send-btn:disabled { opacity: .4; cursor: not-allowed; }

/* Transitions */
.chat-slide-enter-active, .chat-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.chat-slide-enter-from, .chat-slide-leave-to {
  opacity: 0; transform: translateY(16px) scale(0.97);
}
.icon-swap-enter-active, .icon-swap-leave-active { transition: all .15s ease; }
.icon-swap-enter-from, .icon-swap-leave-to { opacity: 0; transform: scale(.7) rotate(30deg); }
</style>
