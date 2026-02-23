<template>
  <div v-if="course">
    <CourseHero :course="course" />

    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in TABS"
        :key="tab.id"
        class="tab"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab panels -->
    <MaterialsTab
      v-if="activeTab === 'materials'"
      :course="course"
      @preview="previewFile = $event"
      @upload="showUpload = true"
    />

    <AssignmentsTab
      v-if="activeTab === 'assignments'"
      :course="course"
      @ai-help="aiHelpTarget = $event"
    />

    <AiPlanTab
      v-if="activeTab === 'aiplan'"
      :course-id="course.id"
    />

    <!-- Modals -->
    <FilePreviewModal v-if="previewFile" :file="previewFile" @close="previewFile = null" />
    <UploadModal     v-if="showUpload"   @close="showUpload = false" />
    <AiHelpModal
      v-if="aiHelpTarget"
      :assignment="aiHelpTarget"
      @close="aiHelpTarget = null"
      @open-chat="aiHelpTarget = null"
    />
  </div>

  <!-- 404 state -->
  <div v-else class="not-found">
    <div class="not-found-icon">🔍</div>
    <div class="not-found-title">Курс не найден</div>
    <RouterLink to="/" class="btn btn-primary" style="margin-top: 12px">На главную</RouterLink>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

import CourseHero      from '@/components/course/CourseHero.vue'
import MaterialsTab    from '@/components/course/MaterialsTab.vue'
import AssignmentsTab  from '@/components/course/AssignmentsTab.vue'
import AiPlanTab       from '@/components/course/AiPlanTab.vue'
import FilePreviewModal from '@/components/modals/FilePreviewModal.vue'
import UploadModal     from '@/components/modals/UploadModal.vue'
import AiHelpModal     from '@/components/modals/AiHelpModal.vue'

const route = useRoute()
const store = useWorkspaceStore()

const TABS = [
  { id: 'materials',   label: '📂 Материалы' },
  { id: 'assignments', label: '📋 Задания' },
  { id: 'aiplan',      label: '🤖 ИИ-План' },
]

const activeTab     = ref('materials')
const previewFile   = ref(null)
const showUpload    = ref(false)
const aiHelpTarget  = ref(null)

const course = computed(() =>
  store.courses.find((c) => String(c.id) === String(route.params.id))
)

// Reset tab when navigating between courses
watch(() => route.params.id, () => { activeTab.value = 'materials' })
</script>

<style scoped>
.tabs {
  display: flex; gap: 2px;
  background: var(--surface-2); border-radius: var(--radius-sm);
  padding: 3px; margin-bottom: 20px;
}
.tab {
  flex: 1; text-align: center; padding: 8px 14px;
  border-radius: 6px; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: background var(--transition), color var(--transition);
  color: var(--text-muted); border: none; background: transparent;
  font-family: var(--font-body);
}
.tab.active {
  background: var(--surface); color: var(--text-primary);
  box-shadow: 0 1px 3px rgba(26,23,20,0.08);
}
.tab:hover:not(.active) { color: var(--text-secondary); }

.not-found {
  display: flex; flex-direction: column; align-items: center;
  padding: 80px 20px; text-align: center; color: var(--text-muted);
}
.not-found-icon  { font-size: 48px; margin-bottom: 12px; }
.not-found-title { font-size: 16px; font-weight: 500; }
</style>
