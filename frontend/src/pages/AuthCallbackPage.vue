<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="text-center">
      <h2 class="text-2xl font-bold mb-4">Completing sign in...</h2>
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  // Auth state will be updated by Supabase listener
  await new Promise(resolve => setTimeout(resolve, 1000))

  if (authStore.isAuthenticated) {
    router.push('/')
  } else {
    router.push('/login')
  }
})
</script>
