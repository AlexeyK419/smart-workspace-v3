<template>
  <div>
    <div class="page-title">Добро пожаловать, {{ store.currentUser.name.split(' ')[0] }} 👋</div>
    <div class="page-sub">{{ todayString }}</div>

    <StatsRow />

    <div class="dashboard-grid">
      <!-- Left column -->
      <div>
        <CalendarWidget />
        <ScheduleToday />
      </div>

      <!-- Right column -->
      <UpcomingAssignments />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import StatsRow            from '@/components/dashboard/StatsRow.vue'
import CalendarWidget      from '@/components/dashboard/CalendarWidget.vue'
import ScheduleToday       from '@/components/dashboard/ScheduleToday.vue'
import UpcomingAssignments from '@/components/dashboard/UpcomingAssignments.vue'

const store = useWorkspaceStore()

const todayString = computed(() =>
  new Date().toLocaleDateString('ru-RU', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
)
</script>

<style scoped>
.page-title {
  font-family: var(--font-display);
  font-size: 26px; font-weight: 600;
  margin-bottom: 6px; letter-spacing: -0.5px;
}
.page-sub { color: var(--text-muted); font-size: 13.5px; margin-bottom: 24px; }

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
}
</style>
