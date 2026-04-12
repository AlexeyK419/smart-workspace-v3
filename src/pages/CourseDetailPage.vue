<template>
  <div v-if="course">
    <CourseHero :course="course" @edit="showEditCourse = true" @delete="handleDeleteCourse" />

    <!-- Edit Course inline form -->
    <Transition name="form-slide">
      <div v-if="showEditCourse" class="card edit-course-form">
        <div class="edit-title">Редактировать курс</div>
        <div class="form-row">
          <div class="form-group" style="flex:2">
            <label class="form-label">Название *</label>
            <input class="form-input" v-model="editForm.name" />
          </div>
          <div class="form-group" style="flex:1">
            <label class="form-label">Преподаватель</label>
            <input class="form-input" v-model="editForm.teacher" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label class="form-label">Семестр</label>
            <input class="form-input" v-model="editForm.semester" />
          </div>
          <div class="form-group" style="flex:1">
            <label class="form-label">Прогресс (%)</label>
            <input class="form-input" type="number" min="0" max="100" v-model.number="editForm.progress" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Цвет</label>
          <div class="color-options">
            <div v-for="c in COLORS" :key="c" class="color-opt"
              :class="{ selected: editForm.color === c }"
              :style="{ background: c }"
              @click="editForm.color = c"></div>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-ghost" @click="showEditCourse = false">Отмена</button>
          <button class="btn btn-primary" :disabled="!editForm.name" @click="saveEditCourse">Сохранить</button>
        </div>
      </div>
    </Transition>

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
      :saved-plan="course.ai_plan || ''"
    />

    <!-- Modals -->
    <FilePreviewModal v-if="previewFile" :file="previewFile" @close="previewFile = null" />
    <UploadModal      v-if="showUpload"  @close="showUpload = false" />
    <AiHelpModal
      v-if="aiHelpTarget"
      :assignment="aiHelpTarget"
      @close="aiHelpTarget = null"
      @open-chat="aiHelpTarget = null"
    />
  </div>

  <!-- 404 state -->
  <div v-else class="not-found">
    <div class="not-found-icon">😕</div>
    <div class="not-found-title">Курс не найден</div>
    <RouterLink to="/" class="btn btn-primary" style="margin-top: 12px">На главную</RouterLink>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

import CourseHero      from '@/components/course/CourseHero.vue'
import MaterialsTab    from '@/components/course/MaterialsTab.vue'
import AssignmentsTab  from '@/components/course/AssignmentsTab.vue'
import AiPlanTab       from '@/components/course/AiPlanTab.vue'
import FilePreviewModal from '@/components/modals/FilePreviewModal.vue'
import UploadModal     from '@/components/modals/UploadModal.vue'
import AiHelpModal     from '@/components/modals/AiHelpModal.vue'

const route  = useRoute()
const router = useRouter()
const store  = useWorkspaceStore()

const TABS = [
  { id: 'materials',   label: '📁 Материалы' },
  { id: 'assignments', label: '📋 Задания' },
  { id: 'aiplan',      label: '🤖 ИИ-План' },
]
const COLORS = ['#3d52d5','#e05c2f','#2d7a4f','#b45309','#7c3aed','#0891b2','#db2777','#64748b']

const activeTab      = ref('materials')
const previewFile    = ref(null)
const showUpload     = ref(false)
const aiHelpTarget   = ref(null)
const showEditCourse = ref(false)

const editForm = reactive({ name: '', teacher: '', semester: '', progress: 0, color: '#3d52d5' })

const course = computed(() =>
  store.courses.find((c) => String(c.id) === String(route.params.id))
)

watch(() => route.params.id, () => { activeTab.value = 'materials'; showEditCourse.value = false })

watch(showEditCourse, (v) => {
  if (v && course.value) {
    Object.assign(editForm, {
      name: course.value.name,
      teacher: course.value.teacher,
      semester: course.value.semester,
      progress: course.value.progress,
      color: course.value.color,
    })
  }
})

async function saveEditCourse() {
  if (!editForm.name || !course.value) return
  await store.updateCourse(course.value.id, { ...editForm })
  showEditCourse.value = false
}

async function handleDeleteCourse() {
  if (!course.value) return
  if (!confirm(`Удалить курс «${course.value.name}»? Все материалы и задания будут удалены.`)) return
  await store.deleteCourse(course.value.id)
  router.push('/')
}
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

/* Edit course form */
.edit-course-form { margin-bottom: 20px; padding: 18px; border: 1.5px solid var(--accent-mid); }
.edit-title { font-weight: 600; font-size: 14px; margin-bottom: 14px; color: var(--accent); }
.form-row { display: flex; gap: 12px; margin-bottom: 12px; }
.form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }
.color-options { display: flex; gap: 8px; flex-wrap: wrap; }
.color-opt {
  width: 24px; height: 24px; border-radius: 50%; cursor: pointer;
  border: 2px solid transparent;
  transition: border-color var(--transition), transform var(--transition);
}
.color-opt.selected, .color-opt:hover { border-color: var(--text-primary); transform: scale(1.15); }
.form-slide-enter-active, .form-slide-leave-active { transition: all 0.25s ease; }
.form-slide-enter-from, .form-slide-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
