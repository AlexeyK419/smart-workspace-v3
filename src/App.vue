<template>
  <MainLayout>
    <router-view />
  </MainLayout>

  <AddCourseModal v-if="showAddCourse" @close="showAddCourse = false" />

  <Transition name="toast">
    <div v-if="store.toast" class="toast">{{ store.toast }}</div>
  </Transition>

  <AiChatWidget />
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import AddCourseModal from '@/components/modals/AddCourseModal.vue'
import AiChatWidget from '@/components/widgets/AiChatWidget.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
const showAddCourse = ref(false)

provide('openAddCourse', () => (showAddCourse.value = true))

onMounted(async () => {
  await Promise.all([store.fetchCourses(), store.fetchSchedule()])
})
</script>

<style scoped>
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
