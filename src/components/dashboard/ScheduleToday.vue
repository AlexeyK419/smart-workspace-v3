<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Расписание сегодня</div>
      <button class="btn btn-ghost" style="padding: 5px 10px; font-size: 12px">Все</button>
    </div>

    <div class="events-list">
      <div v-for="ev in store.todayEvents" :key="ev.id" class="event-row">
        <div class="event-time">{{ ev.time }}</div>
        <div
          class="event-body"
          :style="{
            borderLeftColor: ev.color,
            background: ev.color + '18',
          }"
        >
          <div class="event-title">{{ ev.title }}</div>
          <div class="event-location">{{ ev.location }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useWorkspaceStore } from '@/stores/workspace'
const store = useWorkspaceStore()
</script>

<style scoped>
.events-list { display: flex; flex-direction: column; gap: 10px; }

.event-row { display: flex; gap: 12px; align-items: flex-start; }

.event-time {
  font-size: 11px; color: var(--text-muted);
  width: 44px; flex-shrink: 0; margin-top: 2px; font-weight: 500;
}

.event-body {
  flex: 1; padding: 10px 12px;
  border-radius: 8px; border-left: 3px solid;
}

.event-title    { font-size: 13px; font-weight: 600; }
.event-location { font-size: 11.5px; color: var(--text-muted); margin-top: 2px; }
</style>
