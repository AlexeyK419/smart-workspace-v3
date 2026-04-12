<template>
  <div class="settings-page">
    <section class="settings-hero">
      <div>
        <div class="page-title">Настройки</div>
        <div class="page-sub">Управляйте внешним видом приложения и параметрами аккаунта в одном месте.</div>
      </div>
      <div class="hero-pills">
        <div class="hero-pill">
          <span>Текущая тема</span>
          <strong>{{ uiStore.theme === 'dark' ? 'Темная' : 'Светлая' }}</strong>
        </div>
        <div class="hero-pill">
          <span>Аккаунт</span>
          <strong>{{ authStore.currentUser?.email || 'Без email' }}</strong>
        </div>
      </div>
    </section>

    <div class="settings-grid">
      <section class="card settings-card">
        <div class="card-head">
          <div>
            <div class="card-title">Оформление</div>
            <div class="card-sub">Переключайте тему без перезагрузки страницы.</div>
          </div>
        </div>

        <div class="theme-picker">
          <button
            class="theme-option"
            :class="{ active: uiStore.theme === 'light' }"
            type="button"
            @click="uiStore.applyTheme('light')"
          >
            <span class="theme-swatch light"></span>
            <span>
              <strong>Светлая</strong>
              <small>Нейтральный рабочий режим для дневного использования.</small>
            </span>
          </button>

          <button
            class="theme-option"
            :class="{ active: uiStore.theme === 'dark' }"
            type="button"
            @click="uiStore.applyTheme('dark')"
          >
            <span class="theme-swatch dark"></span>
            <span>
              <strong>Темная</strong>
              <small>Мягкий контраст для работы вечером и в затемненной комнате.</small>
            </span>
          </button>
        </div>
      </section>

      <section class="card settings-card">
        <div class="card-head">
          <div>
            <div class="card-title">Профиль</div>
            <div class="card-sub">Измените отображаемое имя в приложении.</div>
          </div>
        </div>

        <form class="settings-form" @submit.prevent="saveProfile">
          <label class="form-group">
            <span class="form-label">Имя</span>
            <input v-model.trim="profileForm.name" class="input" type="text" placeholder="Ваше имя" />
          </label>

          <label class="form-group">
            <span class="form-label">Email</span>
            <input :value="authStore.currentUser?.email || ''" class="input" type="email" disabled />
          </label>

          <div class="form-actions">
            <button class="btn btn-ghost" type="button" @click="resetProfile">Сбросить</button>
            <button class="btn btn-primary" type="submit" :disabled="profileSaving || !profileForm.name">
              {{ profileSaving ? 'Сохраняем…' : 'Сохранить имя' }}
            </button>
          </div>
        </form>
      </section>

      <section class="card settings-card full-width">
        <div class="card-head">
          <div>
            <div class="card-title">Безопасность</div>
            <div class="card-sub">Смените пароль для входа в аккаунт.</div>
          </div>
        </div>

        <form class="settings-form password-grid" @submit.prevent="savePassword">
          <label class="form-group">
            <span class="form-label">Текущий пароль</span>
            <input v-model="passwordForm.current_password" class="input" type="password" placeholder="Введите текущий пароль" />
          </label>

          <label class="form-group">
            <span class="form-label">Новый пароль</span>
            <input v-model="passwordForm.new_password" class="input" type="password" placeholder="Минимум 6 символов" />
          </label>

          <label class="form-group">
            <span class="form-label">Повтор нового пароля</span>
            <input v-model="passwordForm.repeat_password" class="input" type="password" placeholder="Повторите новый пароль" />
          </label>

          <div class="form-actions full-span">
            <button class="btn btn-ghost" type="button" @click="resetPassword">Очистить</button>
            <button class="btn btn-primary" type="submit" :disabled="passwordSaving">
              {{ passwordSaving ? 'Обновляем…' : 'Изменить пароль' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'
import { useUiStore } from '@/stores/ui'

const authStore = useAuthStore()
const workspaceStore = useWorkspaceStore()
const uiStore = useUiStore()

const profileSaving = ref(false)
const passwordSaving = ref(false)

const profileForm = reactive({
  name: '',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  repeat_password: '',
})

watch(
  () => authStore.currentUser,
  (user) => {
    profileForm.name = user?.name || ''
  },
  { immediate: true }
)

function resetProfile() {
  profileForm.name = authStore.currentUser?.name || ''
}

function resetPassword() {
  passwordForm.current_password = ''
  passwordForm.new_password = ''
  passwordForm.repeat_password = ''
}

async function saveProfile() {
  if (!profileForm.name) return
  profileSaving.value = true
  try {
    await authStore.updateProfile({ name: profileForm.name })
    workspaceStore.showToast('Имя обновлено')
  } catch (error) {
    workspaceStore.showToast(`Ошибка обновления профиля: ${error.message}`)
  } finally {
    profileSaving.value = false
  }
}

async function savePassword() {
  if (!passwordForm.current_password || !passwordForm.new_password) {
    workspaceStore.showToast('Заполните все поля пароля')
    return
  }

  if (passwordForm.new_password !== passwordForm.repeat_password) {
    workspaceStore.showToast('Новый пароль и подтверждение не совпадают')
    return
  }

  passwordSaving.value = true
  try {
    await authStore.updatePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    resetPassword()
    workspaceStore.showToast('Пароль обновлён')
  } catch (error) {
    workspaceStore.showToast(`Ошибка смены пароля: ${error.message}`)
  } finally {
    passwordSaving.value = false
  }
}
</script>

<style scoped>
.settings-page {
  display: grid;
  gap: 20px;
}

.settings-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 380px);
  gap: 18px;
  padding: 26px 28px;
  border: 1px solid var(--border);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--accent) 12%, transparent) 0%, transparent 32%),
    linear-gradient(145deg, color-mix(in srgb, var(--surface) 92%, white) 0%, var(--surface) 100%);
  box-shadow: var(--shadow-lg);
}

.page-title {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 600;
  margin-bottom: 6px;
}

.page-sub,
.card-sub,
.hero-pill span,
.theme-option small {
  color: var(--text-muted);
}

.hero-pills {
  display: grid;
  gap: 12px;
}

.hero-pill {
  padding: 14px 16px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface) 90%, transparent);
  border: 1px solid var(--border-soft);
  display: grid;
  gap: 4px;
}

.hero-pill strong {
  font-size: 16px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.settings-card {
  display: grid;
  gap: 18px;
  border-radius: 24px;
}

.settings-card.full-width {
  grid-column: 1 / -1;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.theme-picker {
  display: grid;
  gap: 12px;
}

.theme-option {
  width: 100%;
  border: 1px solid var(--border);
  background: var(--surface-2);
  border-radius: 20px;
  padding: 16px;
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  gap: 14px;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition);
}

.theme-option.active {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 8%, var(--surface));
  box-shadow: 0 12px 28px color-mix(in srgb, var(--accent) 14%, transparent);
}

.theme-option strong {
  display: block;
  margin-bottom: 4px;
}

.theme-swatch {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  border: 1px solid var(--border);
}

.theme-swatch.light {
  background: linear-gradient(180deg, #f9f7f2 0%, #ffffff 100%);
}

.theme-swatch.dark {
  background: linear-gradient(180deg, #1f2430 0%, #10141d 100%);
  border-color: rgba(255, 255, 255, 0.08);
}

.settings-form {
  display: grid;
  gap: 14px;
}

.password-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: end;
}

.form-group {
  display: grid;
  gap: 8px;
}

.form-label {
  font-size: 12px;
  color: var(--text-muted);
}

.input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 14px;
  background: var(--surface);
  color: var(--text-primary);
}

.input:focus {
  outline: none;
  border-color: var(--accent-mid);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
}

.input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  align-items: center;
}

.full-span {
  grid-column: 1 / -1;
}

@media (max-width: 1100px) {
  .settings-hero,
  .settings-grid,
  .password-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .settings-hero,
  .settings-card {
    padding: 18px;
  }

  .form-actions {
    display: grid;
  }
}
</style>
