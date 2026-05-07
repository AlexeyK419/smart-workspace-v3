<template>
  <div class="welcome-shell">
    <div class="welcome-hero">
      <div class="hero-badge">Интеллектуальное учебное пространство</div>
      <h1>Управляй учёбой в одном месте</h1>
      <p>
        Курсы, материалы, дедлайны, компактный календарь, расписание и встроенный помощник —
        всё в одном рабочем пространстве.
      </p>

      <div class="hero-points">
        <div class="point-card">
          <span>📚</span>
          <div>
            <strong>Личные курсы</strong>
            <p>Каждый пользователь видит только свои предметы, задания и материалы.</p>
          </div>
        </div>
        <div class="point-card">
          <span>🗓️</span>
          <div>
            <strong>Дедлайны и расписание</strong>
            <p>Расписание сохраняется в базе, а ближайшие сроки всегда под рукой.</p>
          </div>
        </div>
        <div class="point-card">
          <span>✨</span>
          <div>
            <strong>Ассистент платформы</strong>
            <p>Помогает разбираться в темах и планировать подготовку без готовых ответов.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="auth-card">
      <div class="auth-tabs">
        <button :class="['auth-tab', { active: mode === 'login' }]" @click="switchMode('login')">Войти</button>
        <button :class="['auth-tab', { active: mode === 'register' }]" @click="switchMode('register')">Регистрация</button>
      </div>

      <form v-if="mode === 'login'" class="auth-form" @submit.prevent="submitLogin">
        <h2>С возвращением</h2>
        <p class="auth-sub">Войдите в аккаунт, чтобы продолжить с того места, где остановились.</p>

        <label>
          <span>Email</span>
          <input v-model.trim="loginForm.email" type="email" placeholder="you@example.com" required />
        </label>

        <label>
          <span>Пароль</span>
          <input v-model="loginForm.password" type="password" placeholder="Минимум 6 символов" required />
        </label>

        <div v-if="error" class="auth-error">{{ error }}</div>
        <button class="auth-submit" :disabled="submitting">Войти</button>
      </form>

      <form v-else class="auth-form" @submit.prevent="submitRegister">
        <h2>Создайте аккаунт</h2>
        <p class="auth-sub">После регистрации вы сразу попадёте в своё личное учебное пространство.</p>

        <label>
          <span>Имя</span>
          <input v-model.trim="registerForm.name" type="text" placeholder="Алексей Иванов" required />
        </label>

        <label>
          <span>Email</span>
          <input v-model.trim="registerForm.email" type="email" placeholder="you@example.com" required />
        </label>

        <label>
          <span>Роль / курс</span>
          <input v-model.trim="registerForm.role" type="text" placeholder="Студент" />
        </label>

        <label>
          <span>Пароль</span>
          <input v-model="registerForm.password" type="password" placeholder="Минимум 6 символов" required />
        </label>

        <label>
          <span>Повторите пароль</span>
          <input v-model="registerForm.passwordRepeat" type="password" placeholder="Повторите пароль" required />
        </label>

        <div v-if="error" class="auth-error">{{ error }}</div>
        <button class="auth-submit" :disabled="submitting">Зарегистрироваться</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref('login')
const error = ref('')
const submitting = ref(false)

const loginForm = ref({
  email: '',
  password: '',
})

const registerForm = ref({
  name: '',
  email: '',
  role: 'Студент',
  password: '',
  passwordRepeat: '',
})

function switchMode(nextMode) {
  mode.value = nextMode
  error.value = ''
}

async function submitLogin() {
  error.value = ''
  submitting.value = true
  try {
    const user = await authStore.login(loginForm.value)
    router.replace((user.role || '').toLowerCase() === 'administrator' ? '/admin' : '/')
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

async function submitRegister() {
  error.value = ''
  if (registerForm.value.password !== registerForm.value.passwordRepeat) {
    error.value = 'Пароли не совпадают'
    return
  }

  submitting.value = true
  try {
    await authStore.register({
      name: registerForm.value.name,
      email: registerForm.value.email,
      role: registerForm.value.role || 'Студент',
      password: registerForm.value.password,
    })
    router.replace('/')
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.welcome-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) 460px;
  gap: 28px;
  width: 100%;
  max-width: 1240px;
  padding: 28px;
  margin: 0 auto;
  align-items: center;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--accent) 18%, transparent), transparent 34%),
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--bg) 90%, var(--surface)) 0%,
      color-mix(in srgb, var(--bg) 96%, var(--surface-2)) 100%
    );
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface) 82%, transparent);
  border: 1px solid var(--border-soft);
  color: var(--accent);
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 18px;
}
.welcome-hero,
.auth-card {
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  backdrop-filter: blur(14px);
  border: 1px solid var(--border-soft);
  border-radius: 30px;
  box-shadow: var(--shadow-lg);
}
.welcome-hero {
  padding: 46px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.welcome-hero h1 {
  font-family: var(--font-display);
  font-size: clamp(36px, 4vw, 56px);
  line-height: 1.02;
  margin: 0 0 18px;
  letter-spacing: -0.05em;
}
.welcome-hero > p {
  max-width: 640px;
  color: var(--text-secondary);
  font-size: 17px;
  line-height: 1.7;
  margin-bottom: 30px;
}
.hero-points {
  display: grid;
  gap: 16px;
}
.point-card {
  display: grid;
  grid-template-columns: 46px 1fr;
  gap: 14px;
  align-items: start;
  padding: 18px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--surface-2) 84%, transparent);
  border: 1px solid var(--border-soft);
}
.point-card span {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--surface);
  font-size: 22px;
}
.point-card strong {
  display: block;
  margin-bottom: 6px;
}
.point-card p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}
.auth-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  justify-self: center;
  width: 100%;
  max-width: 460px;
}
.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 18px;
}
.auth-tab {
  height: 46px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: transparent;
  font-weight: 600;
  cursor: pointer;
}
.auth-tab.active {
  background: color-mix(in srgb, var(--surface-2) 92%, transparent);
  color: var(--text-primary);
  border-color: var(--border);
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
}
.auth-form h2 {
  font-family: var(--font-display);
  font-size: 30px;
  margin: 2px 0 0;
}
.auth-sub {
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0 0 6px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
label span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
input {
  height: 50px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: color-mix(in srgb, var(--surface) 92%, transparent);
  color: var(--text-primary);
  padding: 0 14px;
  font-size: 14px;
  outline: none;
  transition: border-color .2s ease, box-shadow .2s ease;
}
input::placeholder {
  color: var(--text-muted);
}
input:focus {
  border-color: var(--accent);
  background: var(--surface);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 18%, transparent);
}
.auth-submit {
  height: 52px;
  border: 0;
  border-radius: 16px;
  background: var(--accent);
  color: white;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 4px;
}
.auth-submit:disabled {
  opacity: .7;
  cursor: wait;
}
.auth-error {
  border-radius: 14px;
  background: var(--danger-bg);
  border: 1px solid color-mix(in srgb, var(--danger) 30%, transparent);
  color: var(--danger);
  padding: 12px 14px;
  font-size: 13px;
}
.auth-hint {
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface-2) 88%, transparent);
  color: var(--text-secondary);
  font-size: 12.5px;
  line-height: 1.6;
  padding: 12px 14px;
}

@media (max-width: 1100px) {
  .welcome-shell {
    grid-template-columns: 1fr;
    align-content: center;
  }
  .welcome-hero {
    padding: 28px;
  }
}

html[data-theme='dark'] .auth-tab.active {
  background: color-mix(in srgb, var(--surface-2) 82%, #000 18%);
  border-color: color-mix(in srgb, var(--border) 80%, #000 20%);
}
</style>
