<template>
  <section class="chats-page">
    <div class="chats-head">
      <div>
        <div class="eyebrow">Личные сообщения</div>
        <h1>Чаты</h1>
        <p>{{ conversationsLabel }}</p>
      </div>
      <div class="connection-status" :class="chatStore.connectionState">
        <span></span>
        {{ connectionLabel }}
      </div>
    </div>

    <div class="messenger-shell">
      <aside class="dialog-panel">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Имя или email"
            autocomplete="off"
          />
          <button v-if="searchQuery" type="button" aria-label="Очистить поиск" @click="clearSearch">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.3 5.71 12 12l6.3 6.29-1.41 1.41L10.59 13.41 4.29 19.7 2.88 18.29 9.17 12 2.88 5.71 4.29 4.3l6.3 6.29 6.3-6.29z"/></svg>
          </button>
        </div>

        <div v-if="searchQuery.trim().length >= 2" class="search-results">
          <div v-if="isSearching" class="mini-state">Ищем пользователей...</div>
          <template v-else>
            <button
              v-for="user in searchResults"
              :key="user.id"
              class="user-result"
              type="button"
              @click="startChat(user)"
            >
              <div class="avatar" :style="avatarStyle(user.id)">{{ user.initials }}</div>
              <div class="result-copy">
                <strong>{{ user.name }}</strong>
                <span>{{ user.email || 'Без email' }}</span>
              </div>
              <span class="result-action">{{ chatWithUser(user.id) ? 'Открыть' : 'Создать' }}</span>
            </button>
          </template>
          <div v-if="!isSearching && !searchResults.length" class="mini-state">Ничего не найдено</div>
        </div>

        <div class="dialogs-head">
          <span>Диалоги</span>
          <strong>{{ chatStore.chats.length }}</strong>
        </div>

        <div class="dialogs-list">
          <div v-if="chatStore.isLoading" class="dialog-empty">Загружаем чаты...</div>
          <div v-else-if="!chatStore.chats.length" class="dialog-empty">
            <strong>Пока нет диалогов</strong>
            <span>Новые переписки появятся здесь.</span>
          </div>

          <template v-else>
            <button
              v-for="chat in chatStore.chats"
              :key="chat.id"
              type="button"
              class="dialog-card"
              :class="{ active: selectedChat?.id === chat.id, unread: chat.unread_count > 0 }"
              @click="selectChat(chat)"
            >
              <div class="avatar" :style="avatarStyle(chat.peer?.id)">{{ chat.peer?.initials || 'US' }}</div>
              <div class="dialog-copy">
                <div class="dialog-title">
                  <strong>{{ chat.peer?.name || 'Пользователь' }}</strong>
                  <span>{{ formatDialogTime(chat.last_message?.created_at || chat.updated_at) }}</span>
                </div>
                <div class="dialog-preview">
                  <span>{{ lastMessagePreview(chat) }}</span>
                  <b v-if="chat.unread_count">{{ chat.unread_count > 99 ? '99+' : chat.unread_count }}</b>
                </div>
              </div>
            </button>
          </template>
        </div>
      </aside>

      <section class="conversation-panel" :class="{ empty: !selectedChat }">
        <template v-if="selectedChat">
          <header class="conversation-top">
            <div class="peer-main">
              <div class="avatar large" :style="avatarStyle(selectedChat.peer?.id)">
                {{ selectedChat.peer?.initials || 'US' }}
              </div>
              <div>
                <h2>{{ selectedChat.peer?.name || 'Пользователь' }}</h2>
                <span>{{ conversationStatus }}</span>
              </div>
            </div>
            <button
              v-if="selectedChat.unread_count"
              class="ghost-icon-btn"
              type="button"
              title="Отметить прочитанным"
              @click="chatStore.markRead(selectedChat.id)"
            >
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18 7 9.5 15.5 6 12l-1.4 1.4 4.9 4.9L19.4 8.4z"/></svg>
            </button>
          </header>

          <div ref="threadRef" class="message-thread">
            <div v-if="chatStore.messagesLoading" class="thread-state">Загружаем сообщения...</div>
            <div v-else-if="!selectedMessages.length" class="thread-state">
              <strong>История пуста</strong>
              <span>Первое сообщение появится здесь.</span>
            </div>

            <template v-else>
              <div
                v-for="message in selectedMessages"
                :key="message.id"
                class="message-row"
                :class="{ self: message.sender_id === authStore.currentUser?.id }"
              >
                <div
                  v-if="message.sender_id !== authStore.currentUser?.id"
                  class="avatar small"
                  :style="avatarStyle(message.sender_id)"
                >
                  {{ message.sender?.initials || selectedChat.peer?.initials || 'US' }}
                </div>
                <div class="message-stack">
                  <div class="message-meta">
                    <strong>{{ message.sender_id === authStore.currentUser?.id ? 'Вы' : (message.sender?.name || selectedChat.peer?.name) }}</strong>
                    <span>{{ formatMessageTime(message.created_at) }}</span>
                  </div>
                  <div class="message-bubble">
                    <p>{{ message.body }}</p>
                  </div>
                </div>
              </div>
            </template>

            <div v-if="typingNames.length" class="typing-pill">
              {{ typingNames.join(', ') }} {{ typingNames.length > 1 ? 'печатают...' : 'печатает...' }}
            </div>
          </div>

          <form class="composer" @submit.prevent="sendMessage">
            <textarea
              v-model="messageDraft"
              rows="2"
              placeholder="Сообщение"
              @input="handleTyping"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <button class="send-btn" type="submit" :disabled="!messageDraft.trim() || sending">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M2 21 23 12 2 3v7l15 2-15 2v7z"/></svg>
            </button>
          </form>
        </template>

        <div v-else class="conversation-empty">
          <div class="empty-mark">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16v12H7.17L4 19.17V4Zm2 2v8.34L6.34 14H20V6H6Zm3 3h8v2H9V9Zm0 3h5v2H9v-2Z"/></svg>
          </div>
          <h2>Выберите диалог</h2>
          <p>Сообщения появятся в этом окне.</p>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useChatsStore } from '@/stores/chats'
import { useWorkspaceStore } from '@/stores/workspace'

const chatStore = useChatsStore()
const authStore = useAuthStore()
const workspaceStore = useWorkspaceStore()

const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const messageDraft = ref('')
const sending = ref(false)
const threadRef = ref(null)

let searchTimer = null
let typingTimer = null
let localTyping = false

const selectedChat = computed(() => chatStore.activeChat)
const selectedMessages = computed(() =>
  chatStore.messagesByChat[String(chatStore.activeChatId)] || []
)
const typingNames = computed(() =>
  (chatStore.typingByChat[String(chatStore.activeChatId)] || []).map((item) => item.user_name)
)

const conversationsLabel = computed(() => {
  if (!chatStore.chats.length) return 'Пока нет активных переписок'
  const unread = chatStore.unreadTotal
  return unread ? `${unread} непрочитанных сообщений` : 'Все сообщения прочитаны'
})

const connectionLabel = computed(() => ({
  online: 'Онлайн',
  connecting: 'Подключаемся',
  offline: 'Офлайн',
})[chatStore.connectionState] || 'Офлайн')

const conversationStatus = computed(() => {
  if (typingNames.value.length) return 'Печатает...'
  return selectedChat.value?.peer?.email || 'Личный чат'
})

watch(searchQuery, (value) => {
  clearTimeout(searchTimer)
  const query = value.trim()
  if (query.length < 2) {
    searchResults.value = []
    isSearching.value = false
    return
  }

  isSearching.value = true
  searchTimer = setTimeout(() => runUserSearch(query), 260)
})

watch(
  () => chatStore.activeChatId,
  async (chatId) => {
    if (!chatId) return
    await loadMessages(chatId)
  }
)

watch(
  () => selectedMessages.value.length,
  () => scrollToBottom()
)

watch(
  () => chatStore.chats.length,
  (length) => {
    if (!chatStore.activeChatId && length) {
      chatStore.setActiveChat(chatStore.chats[0].id)
    }
  }
)

onMounted(async () => {
  chatStore.connectSocket()
  if (!chatStore.chats.length) await chatStore.fetchChats()
  if (chatStore.activeChatId) await loadMessages(chatStore.activeChatId)
  else if (chatStore.chats[0]) chatStore.setActiveChat(chatStore.chats[0].id)
})

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  clearTimeout(typingTimer)
  setTyping(false)
  chatStore.setActiveChat(null)
})

async function runUserSearch(query) {
  try {
    searchResults.value = await workspaceStore.searchUsers(query)
  } finally {
    isSearching.value = false
  }
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
}

function chatWithUser(userId) {
  return chatStore.chats.find((chat) => chat.peer?.id === userId)
}

async function startChat(user) {
  const existing = chatWithUser(user.id)
  const chat = existing || await chatStore.createChat(user.id)
  clearSearch()
  selectChat(chat)
}

function selectChat(chat) {
  if (!chat?.id) return
  if (chatStore.activeChatId === chat.id) {
    loadMessages(chat.id)
    return
  }
  setTyping(false)
  messageDraft.value = ''
  chatStore.setActiveChat(chat.id)
}

async function loadMessages(chatId) {
  await chatStore.fetchMessages(chatId)
  scrollToBottom()
}

async function sendMessage() {
  const body = messageDraft.value.trim()
  if (!body || !selectedChat.value || sending.value) return

  sending.value = true
  messageDraft.value = ''
  setTyping(false)
  try {
    await chatStore.sendMessage(selectedChat.value.id, body)
    scrollToBottom()
  } finally {
    sending.value = false
  }
}

function handleTyping() {
  if (!selectedChat.value) return
  if (!messageDraft.value.trim()) {
    setTyping(false)
    return
  }

  setTyping(true)
  clearTimeout(typingTimer)
  typingTimer = setTimeout(() => setTyping(false), 1200)
}

function setTyping(isTyping) {
  if (localTyping === isTyping) return
  localTyping = isTyping
  if (selectedChat.value) chatStore.sendTyping(selectedChat.value.id, isTyping)
}

function scrollToBottom() {
  nextTick(() => {
    if (!threadRef.value) return
    threadRef.value.scrollTop = threadRef.value.scrollHeight
  })
}

function lastMessagePreview(chat) {
  const message = chat.last_message
  if (!message) return 'Нет сообщений'
  const prefix = message.sender_id === authStore.currentUser?.id ? 'Вы: ' : ''
  return `${prefix}${message.body}`.replace(/\s+/g, ' ')
}

function formatDialogTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const today = new Date()
  const sameDay = date.toDateString() === today.toDateString()
  if (sameDay) return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function formatMessageTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function avatarStyle(seed = 0) {
  const colors = ['#3559d8', '#2f7f58', '#bc6a19', '#c4493e', '#0891b2', '#7c3aed']
  return { '--avatar-color': colors[Math.abs(Number(seed) || 0) % colors.length] }
}
</script>

<style scoped>
.chats-page {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
  height: calc(100dvh - var(--header-h) - 56px);
  min-height: 640px;
}

.chats-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: end;
}

.eyebrow {
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.chats-head h1 {
  font-family: var(--font-display);
  font-size: 32px;
  line-height: 1.1;
}

.chats-head p {
  color: var(--text-muted);
  margin-top: 5px;
}

.connection-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 999px;
  padding: 8px 12px;
  color: var(--text-secondary);
  font-weight: 600;
  box-shadow: var(--shadow);
}

.connection-status span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.connection-status.online span { background: var(--success); }
.connection-status.connecting span { background: var(--warning); }
.connection-status.offline span { background: var(--danger); }

.messenger-shell {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
  gap: 18px;
}

.dialog-panel,
.conversation-panel {
  min-height: 0;
  background: color-mix(in srgb, var(--surface) 94%, transparent);
  border: 1px solid var(--border);
  border-radius: 24px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
}

.dialog-panel {
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 14px;
}

.search-box {
  min-height: 46px;
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) 28px;
  align-items: center;
  gap: 8px;
  background: var(--surface-2);
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  padding: 0 10px 0 14px;
}

.search-box svg {
  width: 17px;
  height: 17px;
  color: var(--text-muted);
}

.search-box input {
  border: 0;
  outline: none;
  background: transparent;
  color: var(--text-primary);
}

.search-box button,
.ghost-icon-btn {
  border: 0;
  background: transparent;
  display: grid;
  place-items: center;
  cursor: pointer;
  color: var(--text-muted);
}

.search-results {
  display: grid;
  gap: 8px;
}

.mini-state,
.dialog-empty,
.thread-state {
  border: 1px dashed var(--border);
  border-radius: 18px;
  padding: 16px;
  color: var(--text-muted);
  text-align: center;
}

.dialog-empty {
  display: grid;
  gap: 4px;
}

.dialog-empty strong,
.thread-state strong {
  color: var(--text-primary);
}

.user-result {
  width: 100%;
  border: 1px solid var(--border-soft);
  background: var(--surface);
  border-radius: 18px;
  padding: 10px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  text-align: left;
  cursor: pointer;
}

.user-result:hover {
  background: var(--surface-2);
}

.result-copy,
.dialog-copy {
  min-width: 0;
}

.result-copy strong,
.result-copy span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-copy span,
.dialog-title span,
.dialog-preview span,
.peer-main span,
.message-meta,
.conversation-empty p {
  color: var(--text-muted);
  font-size: 12px;
}

.result-action {
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.dialogs-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.dialogs-head strong {
  color: var(--text-primary);
}

.dialogs-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 9px;
  padding-right: 2px;
}

.dialog-card {
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 20px;
  padding: 12px;
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  text-align: left;
  cursor: pointer;
}

.dialog-card:hover {
  background: var(--surface-2);
}

.dialog-card.active {
  background: color-mix(in srgb, var(--accent) 10%, var(--surface));
  border-color: color-mix(in srgb, var(--accent) 22%, transparent);
}

.dialog-card.unread .dialog-title strong,
.dialog-card.unread .dialog-preview span {
  color: var(--text-primary);
  font-weight: 700;
}

.dialog-title,
.dialog-preview {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.dialog-title strong,
.dialog-preview span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dialog-preview b {
  min-width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 7px;
  background: var(--accent);
  color: #fff;
  font-size: 11px;
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--avatar-color) 14%, var(--surface));
  color: var(--avatar-color);
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
}

.avatar.large {
  width: 54px;
  height: 54px;
  border-radius: 18px;
  font-size: 14px;
}

.avatar.small {
  width: 32px;
  height: 32px;
  border-radius: 11px;
  font-size: 10px;
}

.conversation-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  overflow: hidden;
}

.conversation-panel.empty {
  display: grid;
  place-items: center;
}

.conversation-top {
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-soft);
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.peer-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.peer-main h2 {
  font-size: 18px;
  line-height: 1.25;
}

.ghost-icon-btn {
  width: 38px;
  height: 38px;
  border-radius: 13px;
  border: 1px solid var(--border);
  background: var(--surface);
}

.ghost-icon-btn:hover {
  background: var(--surface-2);
}

.ghost-icon-btn svg {
  width: 18px;
  height: 18px;
}

.message-thread {
  min-height: 0;
  overflow: auto;
  display: grid;
  gap: 12px;
  align-content: start;
  padding: 22px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--surface) 98%, transparent), color-mix(in srgb, var(--surface-2) 92%, transparent));
}

.thread-state {
  align-self: center;
  justify-self: center;
  width: min(360px, 100%);
  display: grid;
  gap: 4px;
  margin-top: 80px;
}

.message-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.message-row.self {
  justify-content: flex-end;
}

.message-stack {
  max-width: min(68%, 720px);
  display: grid;
  gap: 5px;
}

.message-row.self .message-stack {
  justify-items: end;
}

.message-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.message-meta strong {
  color: var(--text-secondary);
}

.message-bubble {
  border: 1px solid var(--border-soft);
  background: var(--surface);
  border-radius: 20px 20px 20px 8px;
  padding: 12px 14px;
  box-shadow: 0 10px 24px rgba(26, 23, 20, 0.05);
}

.message-row.self .message-bubble {
  background: color-mix(in srgb, var(--accent) 14%, var(--surface));
  border-color: transparent;
  border-radius: 20px 20px 8px 20px;
}

.message-bubble p {
  white-space: pre-wrap;
  word-break: break-word;
}

.typing-pill {
  justify-self: start;
  border: 1px solid var(--border-soft);
  background: var(--surface);
  border-radius: 999px;
  padding: 8px 12px;
  color: var(--text-secondary);
  font-size: 12px;
}

.composer {
  border-top: 1px solid var(--border-soft);
  background: color-mix(in srgb, var(--surface) 94%, transparent);
  padding: 14px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 46px;
  gap: 10px;
  align-items: end;
}

.composer textarea {
  width: 100%;
  min-height: 46px;
  max-height: 150px;
  resize: vertical;
  border: 1px solid var(--border);
  outline: none;
  border-radius: 18px;
  padding: 12px 14px;
  background: var(--surface-2);
  color: var(--text-primary);
}

.composer textarea:focus {
  border-color: var(--accent-mid);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 10%, transparent);
}

.send-btn {
  width: 46px;
  height: 46px;
  border: 0;
  border-radius: 16px;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.send-btn svg {
  width: 18px;
  height: 18px;
}

.conversation-empty {
  text-align: center;
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 24px;
}

.empty-mark {
  width: 72px;
  height: 72px;
  border-radius: 24px;
  display: grid;
  place-items: center;
  background: var(--accent-light);
  color: var(--accent);
}

.empty-mark svg {
  width: 32px;
  height: 32px;
}

@media (max-width: 1120px) {
  .messenger-shell {
    grid-template-columns: 320px minmax(0, 1fr);
  }

  .message-stack {
    max-width: min(78%, 620px);
  }
}

@media (max-width: 860px) {
  .chats-page {
    height: auto;
    min-height: 0;
  }

  .chats-head {
    align-items: start;
    flex-direction: column;
  }

  .messenger-shell {
    grid-template-columns: 1fr;
  }

  .dialog-panel {
    max-height: 520px;
  }

  .conversation-panel {
    min-height: 640px;
  }
}

@media (max-width: 560px) {
  .chats-head h1 {
    font-size: 28px;
  }

  .dialog-panel,
  .conversation-panel {
    border-radius: 18px;
  }

  .message-thread {
    padding: 16px;
  }

  .message-stack {
    max-width: 100%;
  }

  .conversation-top {
    padding: 14px;
  }

  .peer-main h2 {
    font-size: 16px;
  }
}
</style>
