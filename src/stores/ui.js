import { defineStore } from 'pinia'
import { ref } from 'vue'

const THEME_KEY = 'workspace_theme'

function getInitialTheme() {
  if (typeof window === 'undefined') return 'light'
  return localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light'
}

export const useUiStore = defineStore('ui', () => {
  const theme = ref(getInitialTheme())

  function applyTheme(nextTheme) {
    const resolved = nextTheme === 'dark' ? 'dark' : 'light'
    theme.value = resolved

    if (typeof document !== 'undefined') {
      document.documentElement.dataset.theme = resolved
      document.documentElement.style.colorScheme = resolved
    }

    if (typeof window !== 'undefined') {
      localStorage.setItem(THEME_KEY, resolved)
    }
  }

  function bootstrapTheme() {
    applyTheme(getInitialTheme())
  }

  function toggleTheme() {
    applyTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return {
    theme,
    applyTheme,
    bootstrapTheme,
    toggleTheme,
  }
})
