import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api, getAuthToken, setAuthToken } from '@/api/index.js'

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref(null)
  const isReady = ref(false)

  const isAuthenticated = computed(() => Boolean(currentUser.value && getAuthToken()))
  const isAdmin = computed(() => (currentUser.value?.role || '').toLowerCase() === 'administrator')

  async function bootstrap() {
    const token = getAuthToken()
    if (!token) {
      isReady.value = true
      return
    }

    try {
      currentUser.value = await api.me()
    } catch {
      setAuthToken('')
      currentUser.value = null
    } finally {
      isReady.value = true
    }
  }

  function applyAuth(authResponse) {
    setAuthToken(authResponse.token)
    currentUser.value = authResponse.user
    return authResponse.user
  }

  async function login(payload) {
    const res = await api.login(payload)
    return applyAuth(res)
  }

  async function register(payload) {
    const res = await api.register(payload)
    return applyAuth(res)
  }

  async function logout() {
    try {
      if (getAuthToken()) await api.logout()
    } catch {
      // ignore backend logout errors and clear client state anyway
    } finally {
      setAuthToken('')
      currentUser.value = null
    }
  }

  async function updateProfile(payload) {
    const updated = await api.updateCurrentUser(payload)
    currentUser.value = updated
    return updated
  }

  async function updatePassword(payload) {
    await api.updatePassword(payload)
  }

  return {
    currentUser,
    isReady,
    isAuthenticated,
    isAdmin,
    bootstrap,
    login,
    register,
    logout,
    updateProfile,
    updatePassword,
  }
})
