<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Расписание сегодня</div>
      <RouterLink to="/schedule" class="btn btn-ghost mini-link">Все</RouterLink>
    </div>

    <div v-if="store.todayEvents.length" class="events-list">
      <div v-for="event in store.todayEvents" :key="event.id" class="event-row">
        <div class="event-time">{{ event.time }}</div>
        <div
          class="event-body"
          :style="{
            borderLeftColor: event.color,
            background: event.color + '18',
          }"
        >
          <div class="event-title">{{ event.title }}</div>
          <div v-if="event.teacher" class="event-teacher">{{ event.teacher }}</div>
          <div class="event-location">{{ event.location || 'Место не указано' }}</div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      На сегодня занятий нет. Добавь их на странице расписания, и они появятся здесь автоматически.
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
</script>

<style scoped>
.mini-link {
  padding: 5px 10px;
  font-size: 12px;
  text-decoration: none;
}
.events-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.event-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.event-time {
  font-size: 11px;
  color: var(--text-muted);
  width: 44px;
  flex-shrink: 0;
  margin-top: 2px;
  font-weight: 600;
}
.event-body {
  flex: 1;
  padding: 10px 12px;
  border-radius: 10px;
  border-left: 3px solid;
}
.event-title {
  font-size: 13px;
  font-weight: 600;
}
.event-location {
  font-size: 11.5px;
  color: var(--text-muted);
  margin-top: 2px;
}
.event-teacher {
  font-size: 11.5px;
  color: var(--text-muted);
  margin-top: 2px;
}
.empty-state {
  padding: 10px 0 2px;
  color: var(--text-muted);
  line-height: 1.6;
}
</style>
