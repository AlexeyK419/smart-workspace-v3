<template>
  <Sidebar :open="sidebarOpen" @close="closeSidebar" />
  <button v-if="sidebarOpen" class="layout-backdrop" type="button" aria-label="Закрыть меню" @click="closeSidebar"></button>

  <div class="main">
    <AppHeader :sidebar-open="sidebarOpen" @toggle-sidebar="toggleSidebar" />
    <div class="content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar   from './Sidebar.vue'
import AppHeader from './AppHeader.vue'

const route = useRoute()
const sidebarOpen = ref(false)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}

watch(() => route.fullPath, closeSidebar)
</script>

<style scoped>
.layout-backdrop {
  position: fixed;
  inset: 0;
  border: 0;
  background: rgba(26, 23, 20, 0.42);
  backdrop-filter: blur(2px);
  z-index: 24;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
  background: var(--bg);
}

@media (min-width: 981px) {
  .layout-backdrop {
    display: none;
  }
}

@media (max-width: 980px) {
  .content {
    padding: 20px 16px 24px;
  }
}
</style>
