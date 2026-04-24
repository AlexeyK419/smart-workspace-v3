import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/api/index.js'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'

function chatSortTime(chat) {
  const value = chat?.last_message?.created_at || chat?.updated_at || chat?.created_at
  const time = value ? new Date(value).getTime() : 0
  return Number.isNaN(time) ? 0 : time
}

function sortChats(items) {
  return [...items].sort((a, b) => chatSortTime(b) - chatSortTime(a))
}

function sortMessages(items) {
  return [...items].sort((a, b) => {
    const aTime = new Date(a.created_at).getTime() || 0
    const bTime = new Date(b.created_at).getTime() || 0
    return aTime - bTime || a.id - b.id
  })
}

export const useChatsStore = defineStore('chats', () => {
  const authStore = useAuthStore()
  const workspaceStore = useWorkspaceStore()

  const chats = ref([])
  const messagesByChat = ref({})
  const activeChatId = ref(null)
  const isLoading = ref(false)
  const messagesLoading = ref(false)
  const connectionState = ref('offline')
  const typingByChat = ref({})

  let socket = null
  let reconnectTimer = null
  let manualClose = true
  const typingTimers = new Map()

  const activeChat = computed(() =>
    chats.value.find((chat) => chat.id === activeChatId.value) || null
  )

  const unreadTotal = computed(() =>
    chats.value.reduce((sum, chat) => sum + Number(chat.unread_count || 0), 0)
  )

  function showError(prefix, error) {
    workspaceStore.showToast(`${prefix}: ${error.message}`)
  }

  function upsertChat(chat) {
    if (!chat?.id) return null
    const idx = chats.value.findIndex((item) => item.id === chat.id)
    if (idx === -1) chats.value = sortChats([chat, ...chats.value])
    else {
      const next = [...chats.value]
      next[idx] = { ...next[idx], ...chat }
      chats.value = sortChats(next)
    }
    return chat
  }

  function appendMessage(message) {
    if (!message?.chat_id) return
    const key = String(message.chat_id)
    const current = messagesByChat.value[key] || []
    if (current.some((item) => item.id === message.id)) return
    messagesByChat.value = {
      ...messagesByChat.value,
      [key]: sortMessages([...current, message]),
    }
  }

  function setActiveChat(chatId) {
    activeChatId.value = chatId ? Number(chatId) : null
  }

  async function fetchChats() {
    if (!authStore.isAuthenticated) {
      chats.value = []
      return []
    }

    isLoading.value = true
    try {
      chats.value = sortChats(await api.getChats())
      return chats.value
    } catch (error) {
      showError('Ошибка загрузки чатов', error)
      return []
    } finally {
      isLoading.value = false
    }
  }

  async function fetchChat(chatId) {
    try {
      const chat = await api.getChat(chatId)
      return upsertChat(chat)
    } catch (error) {
      showError('Ошибка обновления чата', error)
      throw error
    }
  }

  async function createChat(targetUserId) {
    try {
      const chat = await api.createDirectChat({ target_user_id: targetUserId })
      return upsertChat(chat)
    } catch (error) {
      showError('Ошибка создания чата', error)
      throw error
    }
  }

  async function fetchMessages(chatId, options = {}) {
    if (!chatId) return []

    messagesLoading.value = true
    try {
      const messages = await api.getChatMessages(chatId)
      messagesByChat.value = {
        ...messagesByChat.value,
        [String(chatId)]: sortMessages(messages),
      }
      if (options.markRead !== false) await markRead(chatId)
      return messagesByChat.value[String(chatId)]
    } catch (error) {
      showError('Ошибка загрузки сообщений', error)
      throw error
    } finally {
      messagesLoading.value = false
    }
  }

  async function sendMessage(chatId, body) {
    const text = (body || '').trim()
    if (!chatId || !text) return null

    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'message', chat_id: Number(chatId), body: text }))
      return null
    }

    try {
      const message = await api.postChatMessage(chatId, { body: text })
      appendMessage(message)
      await fetchChat(chatId)
      return message
    } catch (error) {
      showError('Ошибка отправки сообщения', error)
      throw error
    }
  }

  async function markRead(chatId) {
    if (!chatId) return null
    try {
      const chat = await api.markChatRead(chatId)
      return upsertChat(chat)
    } catch (error) {
      showError('Ошибка отметки прочтения', error)
      return null
    }
  }

  function sendTyping(chatId, isTyping) {
    if (!chatId || socket?.readyState !== WebSocket.OPEN) return
    socket.send(JSON.stringify({
      type: 'typing',
      chat_id: Number(chatId),
      is_typing: Boolean(isTyping),
    }))
  }

  function setTypingUsers(chatId, users) {
    typingByChat.value = {
      ...typingByChat.value,
      [String(chatId)]: users,
    }
  }

  function clearTyping(chatId = null, userId = null) {
    if (chatId == null) {
      typingTimers.forEach((timer) => clearTimeout(timer))
      typingTimers.clear()
      typingByChat.value = {}
      return
    }

    const chatKey = String(chatId)
    if (userId == null) {
      for (const [key, timer] of typingTimers.entries()) {
        if (key.startsWith(`${chatKey}:`)) {
          clearTimeout(timer)
          typingTimers.delete(key)
        }
      }
      setTypingUsers(chatKey, [])
      return
    }

    const timerKey = `${chatKey}:${userId}`
    const timer = typingTimers.get(timerKey)
    if (timer) clearTimeout(timer)
    typingTimers.delete(timerKey)

    const current = typingByChat.value[chatKey] || []
    setTypingUsers(chatKey, current.filter((item) => item.user_id !== userId))
  }

  function updateTyping(payload) {
    if (!payload?.chat_id || !payload?.user_id || payload.user_id === authStore.currentUser?.id) return

    if (!payload.is_typing) {
      clearTyping(payload.chat_id, payload.user_id)
      return
    }

    clearTyping(payload.chat_id, payload.user_id)
    const chatKey = String(payload.chat_id)
    const current = typingByChat.value[chatKey] || []
    setTypingUsers(chatKey, [
      ...current,
      { user_id: payload.user_id, user_name: payload.user_name || 'Пользователь' },
    ])

    const timerKey = `${chatKey}:${payload.user_id}`
    typingTimers.set(timerKey, setTimeout(() => clearTyping(payload.chat_id, payload.user_id), 1600))
  }

  async function handleSocketPayload(payload) {
    if (payload.type === 'connection.ready') {
      connectionState.value = 'online'
      return
    }

    if (payload.type === 'message.created') {
      if (payload.chat) upsertChat(payload.chat)
      if (payload.message) appendMessage(payload.message)

      const isActive = activeChatId.value === Number(payload.chat_id)
      const isFromPeer = payload.message?.sender_id !== authStore.currentUser?.id
      if (isActive && isFromPeer) await markRead(payload.chat_id)
      return
    }

    if (payload.type === 'chat.updated' && payload.chat) {
      upsertChat(payload.chat)
      return
    }

    if (payload.type === 'typing') {
      updateTyping(payload)
    }
  }

  function connectSocket() {
    if (!authStore.isAuthenticated || typeof window === 'undefined' || typeof WebSocket === 'undefined') return
    if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) return

    manualClose = false
    connectionState.value = 'connecting'
    socket = new WebSocket(api.chatsSocketUrl())

    socket.onopen = () => {
      connectionState.value = 'online'
    }

    socket.onmessage = (event) => {
      try {
        handleSocketPayload(JSON.parse(event.data)).catch(() => {})
      } catch {
        // ignore malformed websocket payloads
      }
    }

    socket.onerror = () => {
      connectionState.value = 'offline'
    }

    socket.onclose = () => {
      socket = null
      connectionState.value = 'offline'
      if (!manualClose && authStore.isAuthenticated) {
        clearTimeout(reconnectTimer)
        reconnectTimer = setTimeout(() => connectSocket(), 1800)
      }
    }
  }

  function disconnectSocket() {
    manualClose = true
    clearTimeout(reconnectTimer)
    clearTyping()
    if (socket) {
      socket.close()
      socket = null
    }
    connectionState.value = 'offline'
  }

  function reset() {
    disconnectSocket()
    chats.value = []
    messagesByChat.value = {}
    activeChatId.value = null
    isLoading.value = false
    messagesLoading.value = false
  }

  return {
    chats,
    messagesByChat,
    activeChatId,
    activeChat,
    isLoading,
    messagesLoading,
    connectionState,
    typingByChat,
    unreadTotal,
    setActiveChat,
    upsertChat,
    appendMessage,
    fetchChats,
    fetchChat,
    createChat,
    fetchMessages,
    sendMessage,
    markRead,
    sendTyping,
    connectSocket,
    disconnectSocket,
    reset,
  }
})
