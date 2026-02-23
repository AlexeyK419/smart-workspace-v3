import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage    from '@/pages/DashboardPage.vue'
import CourseDetailPage from '@/pages/CourseDetailPage.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardPage,
    meta: { breadcrumb: 'Обзор' },
  },
  {
    path: '/course/:id',
    name: 'course',
    component: CourseDetailPage,
    meta: { breadcrumb: 'Курс' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
