<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center max-w-md mx-auto p-8">
      <div v-if="!error">
        <h2 class="text-2xl font-bold mb-4 text-gray-900">Completing sign in...</h2>
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p class="text-gray-600">Please wait while we sign you in with Google.</p>
      </div>

      <div v-else class="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 class="text-xl font-bold mb-2 text-red-900">Sign in failed</h2>
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="router.push('/login')"
          class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
        >
          Back to Login
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { supabase } from '@/lib/supabase'

const router = useRouter()
const authStore = useAuthStore()
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    // Check for OAuth error in URL
    const hashParams = new URLSearchParams(window.location.hash.substring(1))
    const queryParams = new URLSearchParams(window.location.search)

    const errorCode = hashParams.get('error') || queryParams.get('error')
    const errorDescription = hashParams.get('error_description') || queryParams.get('error_description')

    if (errorCode) {
      console.error('OAuth error:', errorCode, errorDescription)
      error.value = errorDescription || 'Authentication failed. Please try again.'
      return
    }

    // Wait for Supabase to exchange the OAuth code/token for a session
    // The SDK automatically handles this with detectSessionInUrl: true
    console.log('Waiting for OAuth session exchange...')

    // Check session multiple times with exponential backoff
    let attempts = 0
    const maxAttempts = 10

    while (attempts < maxAttempts) {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()

      if (sessionError) {
        console.error('Session error:', sessionError)
        error.value = sessionError.message
        return
      }

      if (session) {
        console.log('Session established:', session.user.email)
        // Fetch user data
        await authStore.fetchUser()

        // Redirect to home page
        console.log('Redirecting to home...')
        router.push('/')
        return
      }

      // Wait before next attempt (exponential backoff)
      const delay = Math.min(100 * Math.pow(2, attempts), 2000)
      await new Promise(resolve => setTimeout(resolve, delay))
      attempts++
    }

    // If no session after max attempts, check if user is already authenticated
    if (authStore.isAuthenticated) {
      console.log('Already authenticated, redirecting...')
      router.push('/')
    } else {
      console.error('No session established after', maxAttempts, 'attempts')
      error.value = 'Failed to complete sign in. Please try again.'
    }

  } catch (err) {
    console.error('OAuth callback error:', err)
    error.value = err instanceof Error ? err.message : 'An unexpected error occurred'
  }
})
</script>
