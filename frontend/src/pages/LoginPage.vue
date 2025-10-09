<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to HypePaper
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Track trending research papers with GitHub stars & citations
        </p>
      </div>

      <div class="mt-8 space-y-6">
        <button
          @click="signInWithGoogle"
          :disabled="loading"
          class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <span v-if="!loading">Sign in with Google</span>
          <span v-else>Loading...</span>
        </button>

        <div v-if="error" class="rounded-md bg-red-50 p-4">
          <div class="text-sm text-red-700">{{ error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')

async function signInWithGoogle() {
  loading.value = true
  error.value = ''

  try {
    await authStore.signInWithGoogle()
    // Redirect will happen via OAuth callback
  } catch (err: any) {
    error.value = err.message || 'Failed to sign in'
  } finally {
    loading.value = false
  }
}
</script>
