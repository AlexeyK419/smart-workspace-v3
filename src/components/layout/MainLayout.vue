<template>
  <Sidebar />

  <div class="main">
    <AppHeader />
    <div class="content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import Sidebar   from './Sidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<style scoped>
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
</style>
