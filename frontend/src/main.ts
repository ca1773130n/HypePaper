import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/index.css'
import axios from 'axios'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Configure axios interceptor for auth
axios.interceptors.request.use(async (config) => {
  const authStore = useAuthStore()
  if (authStore.session?.access_token) {
    config.headers.Authorization = `Bearer ${authStore.session.access_token}`
  }
  return config
})

app.mount('#app')
