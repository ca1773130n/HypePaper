import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './assets/index.css'
import App from './App.vue'
import HomePage from './pages/HomePage.vue'
import PaperDetailPage from './pages/PaperDetailPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/papers/:id', component: PaperDetailPage },
  ],
})

createApp(App).use(router).mount('#app')
