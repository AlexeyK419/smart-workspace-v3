<template>
  <main class="admin-shell">
    <section class="admin-panel">
      <header class="admin-header">
        <div>
          <p class="eyebrow">Admin</p>
          <h1>Accounts</h1>
          <p class="subline">All registered users except the admin account.</p>
        </div>
        <button class="logout-btn" type="button" @click="logout">Exit</button>
      </header>

      <div class="summary-row">
        <div class="summary-item">
          <span>{{ users.length }}</span>
          <p>accounts</p>
        </div>
        <div class="summary-item">
          <span>{{ totalCourses }}</span>
          <p>courses</p>
        </div>
        <div class="summary-item">
          <span>{{ totalFiles }}</span>
          <p>files</p>
        </div>
      </div>

      <div v-if="error" class="alert danger">{{ error }}</div>
      <div v-if="success" class="alert success">{{ success }}</div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Courses</th>
              <th>Projects</th>
              <th>Files</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7" class="empty">Loading accounts...</td>
            </tr>
            <tr v-else-if="!users.length">
              <td colspan="7" class="empty">No registered users yet.</td>
            </tr>
            <tr v-for="user in users" :key="user.id">
              <td>
                <div class="user-cell">
                  <span class="avatar">{{ user.initials || initials(user.name) }}</span>
                  <strong>{{ user.name }}</strong>
                </div>
              </td>
              <td>{{ user.email || '-' }}</td>
              <td>{{ user.role || '-' }}</td>
              <td>{{ user.courses_count }}</td>
              <td>{{ user.projects_count }}</td>
              <td>{{ user.files_count }}</td>
              <td class="actions">
                <button
                  class="delete-btn"
                  type="button"
                  :disabled="deletingId === user.id"
                  @click="deleteUser(user)"
                >
                  {{ deletingId === user.id ? 'Deleting...' : 'Delete' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/index.js'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const users = ref([])
const loading = ref(false)
const deletingId = ref(null)
const error = ref('')
const success = ref('')

const totalCourses = computed(() => users.value.reduce((sum, user) => sum + (user.courses_count || 0), 0))
const totalFiles = computed(() => users.value.reduce((sum, user) => sum + (user.files_count || 0), 0))

function initials(name) {
  return (name || 'U')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    users.value = await api.getAdminUsers()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function deleteUser(user) {
  const ok = window.confirm(`Delete account ${user.email || user.name} and all related data?`)
  if (!ok) return

  deletingId.value = user.id
  error.value = ''
  success.value = ''
  try {
    await api.deleteAdminUser(user.id)
    users.value = users.value.filter((item) => item.id !== user.id)
    success.value = 'Account deleted.'
  } catch (e) {
    error.value = e.message
  } finally {
    deletingId.value = null
  }
}

async function logout() {
  await authStore.logout()
  router.replace('/welcome')
}

onMounted(async () => {
  if (!authStore.isAdmin) {
    router.replace('/')
    return
  }
  await loadUsers()
})
</script>

<style scoped>
.admin-shell {
  width: 100%;
  min-height: 100dvh;
  padding: 28px;
  overflow: auto;
  background:
    radial-gradient(circle at 18% 0%, color-mix(in srgb, var(--accent) 12%, transparent), transparent 28%),
    radial-gradient(circle at 84% 8%, color-mix(in srgb, var(--success) 10%, transparent), transparent 24%),
    var(--bg);
}
.admin-panel {
  width: min(1180px, 100%);
  margin: 0 auto;
  background: color-mix(in srgb, var(--surface) 90%, transparent);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow-lg);
  padding: 24px;
}
.admin-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 22px;
}
.eyebrow {
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
h1 {
  font-family: var(--font-display);
  font-size: 38px;
  line-height: 1.1;
  margin: 2px 0 6px;
}
.subline {
  color: var(--text-secondary);
}
.logout-btn,
.delete-btn {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  color: var(--text-primary);
  cursor: pointer;
  font-weight: 700;
  min-height: 38px;
  padding: 0 14px;
}
.logout-btn:hover {
  background: var(--surface-2);
}
.summary-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}
.summary-item {
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface-2) 70%, transparent);
  padding: 14px 16px;
}
.summary-item span {
  display: block;
  font-size: 24px;
  font-weight: 800;
  line-height: 1;
}
.summary-item p {
  color: var(--text-muted);
  margin-top: 6px;
}
.alert {
  border-radius: 10px;
  padding: 11px 13px;
  margin-bottom: 12px;
  font-weight: 600;
}
.alert.danger {
  background: var(--danger-bg);
  color: var(--danger);
}
.alert.success {
  background: var(--success-bg);
  color: var(--success);
}
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border-soft);
  border-radius: 12px;
}
table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
}
th,
td {
  padding: 14px;
  text-align: left;
  border-bottom: 1px solid var(--border-soft);
  vertical-align: middle;
}
th {
  color: var(--text-muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  background: color-mix(in srgb, var(--surface-2) 74%, transparent);
}
tbody tr:last-child td {
  border-bottom: 0;
}
.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 800;
}
.actions {
  text-align: right;
}
.delete-btn {
  border-color: color-mix(in srgb, var(--danger) 32%, var(--border));
  color: var(--danger);
}
.delete-btn:hover:not(:disabled) {
  background: var(--danger-bg);
}
.delete-btn:disabled {
  cursor: wait;
  opacity: 0.65;
}
.empty {
  color: var(--text-muted);
  text-align: center;
  padding: 34px 14px;
}
@media (max-width: 720px) {
  .admin-shell {
    padding: 14px;
  }
  .admin-panel {
    padding: 16px;
    border-radius: 14px;
  }
  .admin-header {
    flex-direction: column;
  }
  .logout-btn {
    width: 100%;
  }
  .summary-row {
    grid-template-columns: 1fr;
  }
}
</style>
