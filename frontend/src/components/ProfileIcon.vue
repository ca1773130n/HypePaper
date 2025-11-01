<template>
  <!-- Authenticated User: Profile Image -->
  <button
    v-if="authStore.isAuthenticated"
    @click="navigateToProfile"
    class="relative group"
    :title="userEmail"
  >
    <!-- Profile Image -->
    <div
      v-if="avatarUrl"
      class="w-10 h-10 rounded-full overflow-hidden border-2 border-white/20 hover:border-purple-500/50 transition-all ring-2 ring-transparent group-hover:ring-purple-500/30"
    >
      <img
        :src="avatarUrl"
        :alt="userName || 'Profile'"
        class="w-full h-full object-cover"
        @error="handleImageError"
      />
    </div>

    <!-- Fallback to Icon if Image Fails -->
    <div
      v-else
      class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center border-2 border-white/20 hover:border-purple-500/50 transition-all ring-2 ring-transparent group-hover:ring-purple-500/30"
    >
      <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    </div>
  </button>

  <!-- Unauthenticated User: Sign In Icon -->
  <button
    v-else
    @click="navigateToLogin"
    class="relative group"
    title="Sign In"
  >
    <div
      class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 flex items-center justify-center shadow-lg shadow-purple-500/50 transition-all ring-2 ring-transparent group-hover:ring-purple-500/50"
    >
      <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
      </svg>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const imageError = ref(false)

// Get user profile data from Supabase/Google OAuth
const avatarUrl = computed(() => {
  if (imageError.value) return null

  const user = authStore.user
  if (!user) return null

  // Try different possible locations for avatar URL
  return user.user_metadata?.avatar_url ||
         user.user_metadata?.picture ||
         user.user_metadata?.avatar ||
         null
})

const userName = computed(() => {
  const user = authStore.user
  if (!user) return null

  return user.user_metadata?.full_name ||
         user.user_metadata?.name ||
         user.email?.split('@')[0] ||
         'User'
})

const userEmail = computed(() => {
  return authStore.user?.email || 'Profile'
})

const handleImageError = () => {
  imageError.value = true
}

const navigateToProfile = () => {
  router.push('/profile')
}

const navigateToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
/* Ensure smooth transitions */
button {
  transition: all 0.2s ease;
}
</style>
