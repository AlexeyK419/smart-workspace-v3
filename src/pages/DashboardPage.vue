<template>
  <div>
    <div class="page-title">Добро пожаловать, {{ firstName }} 👋</div>
    <div class="page-sub">{{ todayString }}</div>

    <StatsRow />

    <div class="dashboard-grid">
      <div class="dashboard-main">
        <CalendarWidget />
        <AiWorkspaceSummaryCard />
      </div>

      <div class="dashboard-side">
        <ScheduleToday />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import StatsRow from '@/components/dashboard/StatsRow.vue'
import CalendarWidget from '@/components/dashboard/CalendarWidget.vue'
import ScheduleToday from '@/components/dashboard/ScheduleToday.vue'
import AiWorkspaceSummaryCard from '@/components/dashboard/AiWorkspaceSummaryCard.vue'

const store = useWorkspaceStore()

const firstName = computed(() => (store.currentUser.name || 'студент').split(' ')[0])
const todayString = computed(() =>
  new Date().toLocaleDateString('ru-RU', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
)
</script>

<style scoped>
.page-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 600;
  margin-bottom: 6px;
  letter-spacing: -0.5px;
}
.page-sub {
  color: var(--text-muted);
  font-size: 13.5px;
  margin-bottom: 24px;
}
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) 360px;
  gap: 20px;
}
.dashboard-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.dashboard-main {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

@media (max-width: 1100px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page-title {
    font-size: 30px;
    line-height: 1.12;
    margin-top: 4px;
  }

  .page-sub {
    margin-bottom: 18px;
  }

  .dashboard-grid,
  .dashboard-main,
  .dashboard-side {
    gap: 14px;
  }
}
</style>
