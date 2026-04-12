<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal" style="max-width: 440px">
      <div class="modal-header">
        <div class="modal-title">Добавить курс</div>
        <button class="modal-close" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Название курса *</label>
          <input class="form-input" v-model="form.name" placeholder="Например: Веб-разработка" />
        </div>
        <div class="form-group">
          <label class="form-label">Преподаватель</label>
          <input class="form-input" v-model="form.teacher" placeholder="Имя преподавателя" />
        </div>
        <div class="form-group">
          <label class="form-label">Семестр</label>
          <input class="form-input" v-model="form.semester" placeholder="Весна 2025" />
        </div>
        <div class="form-group">
          <label class="form-label">Цвет курса</label>
          <div class="color-options">
            <div v-for="c in COLORS" :key="c" class="color-opt"
                 :class="{ selected: form.color === c }"
                 :style="{ background: c }"
                 @click="form.color = c"></div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" @click="emit('close')">Отмена</button>
        <button class="btn btn-primary" :disabled="!form.name || saving" @click="submit">
          {{ saving ? 'Сохранение...' : 'Добавить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const emit  = defineEmits(['close'])
const store = useWorkspaceStore()
const saving = ref(false)

const COLORS = ['#3d52d5','#e05c2f','#2d7a4f','#b45309','#7c3aed','#0891b2','#db2777','#64748b']
const form = reactive({ name: '', teacher: '', semester: 'Весна 2025', color: '#3d52d5' })

async function submit() {
  if (!form.name) return
  saving.value = true
  await store.addCourse({ ...form, emoji: '📚', progress: 0 })
  saving.value = false
  emit('close')
}
</script>

<style scoped>
.color-options { display: flex; gap: 8px; flex-wrap: wrap; }
.color-opt {
  width: 26px; height: 26px; border-radius: 50%; cursor: pointer;
  border: 2px solid transparent;
  transition: border-color var(--transition), transform var(--transition);
}
.color-opt.selected, .color-opt:hover { border-color: var(--text-primary); transform: scale(1.15); }
</style>
