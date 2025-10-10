import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import AuthCallbackPage from '@/pages/AuthCallbackPage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import AdminDashboard from '@/pages/AdminDashboard.vue'
import PaperDetailPage from '@/pages/PaperDetailPage.vue'
import CrawlerPage from '@/pages/CrawlerPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: AuthCallbackPage
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfilePage,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminDashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/papers/:id',
      name: 'paper-detail',
      component: PaperDetailPage
    },
    {
      path: '/crawler',
      name: 'crawler',
      component: CrawlerPage,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
