import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '@/pages/DashboardPage.vue'
import CourseDetailPage from '@/pages/CourseDetailPage.vue'
import SchedulePage from '@/pages/SchedulePage.vue'
import WelcomePage from '@/pages/WelcomePage.vue'
import ProjectsPage from '@/pages/ProjectsPage.vue'
import ProjectDetailPage from '@/pages/ProjectDetailPage.vue'

const routes = [
  {
    path: '/welcome',
    name: 'welcome',
    component: WelcomePage,
    meta: { guestOnly: true },
  },
  {
    path: '/',
    name: 'dashboard',
    component: DashboardPage,
    meta: { breadcrumb: 'Обзор', requiresAuth: true },
  },
  {
    path: '/course/:id',
    name: 'course',
    component: CourseDetailPage,
    meta: { breadcrumb: 'Курс', requiresAuth: true },
  },
  {
    path: '/schedule',
    name: 'schedule',
    component: SchedulePage,
    meta: { breadcrumb: 'Расписание', requiresAuth: true },
  },
  {
    path: '/projects',
    name: 'projects',
    component: ProjectsPage,
    meta: { breadcrumb: 'Проекты', requiresAuth: true },
  },
  {
    path: '/projects/:id',
    name: 'project',
    component: ProjectDetailPage,
    meta: { breadcrumb: 'Проект', requiresAuth: true },
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

router.beforeEach((to) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('workspace_token') : ''

  if (to.meta.requiresAuth && !token) {
    return { name: 'welcome' }
  }

  if (to.meta.guestOnly && token) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
