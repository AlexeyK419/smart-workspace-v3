<template>
  <div class="welcome-shell">
    <div class="welcome-hero">
      <div class="hero-badge">Student OS</div>
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

        <div class="auth-hint">
          Для теста доступен demo-аккаунт: <strong>demo@workspace.local</strong> / <strong>workspace123</strong>
        </div>
      </form>

      <form v-else class="auth-form" @submit.prevent="submitRegister">
        <h2>Создайте аккаунт</h2>
        <p class="auth-sub">После регистрации вы сразу попадёте в своё личное рабочее пространство.</p>

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
  email: 'demo@workspace.local',
  password: 'workspace123',
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
    await authStore.login(loginForm.value)
    router.replace('/')
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
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(61, 82, 213, 0.08), transparent 28%),
    linear-gradient(180deg, #f7f5ef 0%, #f2ede3 100%);
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: var(--accent);
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 18px;
}
.welcome-hero,
.auth-card {
  background: rgba(255, 255, 255, 0.76);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 30px;
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.08);
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
  background: rgba(248, 250, 252, 0.86);
  border: 1px solid rgba(226, 232, 240, 0.9);
}
.point-card span {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: white;
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
  background: var(--text-primary);
  color: white;
  border-color: var(--text-primary);
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
  background: rgba(255, 255, 255, 0.92);
  padding: 0 14px;
  font-size: 14px;
  outline: none;
  transition: border-color .2s ease, box-shadow .2s ease;
}
input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(61, 82, 213, 0.12);
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
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.18);
  color: #b91c1c;
  padding: 12px 14px;
  font-size: 13px;
}
.auth-hint {
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
  color: var(--text-secondary);
  font-size: 12.5px;
  line-height: 1.6;
  padding: 12px 14px;
}

@media (max-width: 1100px) {
  .welcome-shell {
    grid-template-columns: 1fr;
  }
  .welcome-hero {
    padding: 28px;
  }
}
</style>
