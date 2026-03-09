<template>
  <div v-if="!authStore.isReady" class="boot-screen">
    <div class="boot-card">
      <div class="boot-logo">WS</div>
      <div class="boot-title">Smart Student Workspace</div>
      <div class="boot-sub">Подготавливаем ваше пространство…</div>
    </div>
  </div>

  <router-view v-else-if="route.meta.guestOnly" />

  <template v-else>
    <MainLayout>
      <router-view />
    </MainLayout>

    <AddCourseModal v-if="showAddCourse" @close="showAddCourse = false" />

    <Transition name="toast">
      <div v-if="store.toast" class="toast">{{ store.toast }}</div>
    </Transition>

    <AiChatWidget />
  </template>
</template>

<script setup>
import { ref, provide, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'
import AddCourseModal from '@/components/modals/AddCourseModal.vue'
import AiChatWidget from '@/components/widgets/AiChatWidget.vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const store = useWorkspaceStore()
const authStore = useAuthStore()
const showAddCourse = ref(false)

provide('openAddCourse', () => (showAddCourse.value = true))

onMounted(async () => {
  await authStore.bootstrap()
})

watch(
  [() => authStore.isReady, () => authStore.isAuthenticated],
  async ([isReady, isAuthenticated]) => {
    if (!isReady) return

    if (isAuthenticated) {
      await Promise.all([store.fetchCourses(), store.fetchSchedule()])
      if (route.meta.guestOnly) router.replace('/')
    } else {
      store.resetWorkspace()
      if (!route.meta.guestOnly) router.replace('/welcome')
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.boot-screen {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, #f7f5ef 0%, #f3efe5 100%);
}
.boot-card {
  width: min(420px, calc(100vw - 32px));
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 28px;
  padding: 32px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
  text-align: center;
}
.boot-logo {
  width: 58px;
  height: 58px;
  border-radius: 18px;
  margin: 0 auto 16px;
  background: var(--accent);
  color: white;
  display: grid;
  place-items: center;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.boot-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}
.boot-sub {
  color: var(--text-muted);
}
.toast {
  position: fixed;
  bottom: 90px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--text-primary);
  color: white;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 13px;
  z-index: 200;
  white-space: nowrap;
}
</style>
