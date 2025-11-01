<template>
  <!-- Modal Overlay -->
  <Transition name="modal">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @click.self="closeModal"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/70 backdrop-blur-md"
        @click="closeModal"
      ></div>

      <!-- Modal Content -->
      <div
        class="relative bg-[#0A0F1E] rounded-2xl shadow-2xl border border-white/20 max-w-md w-full overflow-hidden"
        @click.stop
      >
        <!-- Animated Background -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
          <div class="absolute top-0 left-1/4 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div class="absolute bottom-0 right-1/4 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-700"></div>
        </div>

        <!-- Close Button -->
        <button
          @click="closeModal"
          class="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/10 transition-all z-10"
          aria-label="Close"
        >
          <svg
            class="w-5 h-5 text-gray-400 hover:text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <!-- Modal Body -->
        <div class="relative p-8">
          <!-- Header -->
          <div class="text-center mb-8">
            <h2 class="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-3">
              Welcome to HypePaper
            </h2>
            <p class="text-gray-400 text-sm">
              Track trending research papers with GitHub stars & citations
            </p>
          </div>

          <!-- Sign In Button -->
          <button
            @click="handleSignIn"
            :disabled="loading"
            class="group relative w-full flex items-center justify-center gap-3 py-3.5 px-6 rounded-xl text-white bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/50 hover:shadow-purple-500/70"
          >
            <!-- Google Icon -->
            <svg
              v-if="!loading"
              class="w-5 h-5"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>

            <!-- Loading Spinner -->
            <svg
              v-else
              class="animate-spin w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>

            <span class="font-medium">
              {{ loading ? 'Signing in...' : 'Sign in with Google' }}
            </span>
          </button>

          <!-- Error Message -->
          <div v-if="error" class="mt-4 rounded-xl bg-red-500/10 border border-red-500/20 p-4">
            <div class="flex items-start gap-3">
              <svg class="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-sm text-red-300">{{ error }}</p>
            </div>
          </div>

          <!-- Footer -->
          <p class="mt-6 text-center text-xs text-gray-500">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')

const closeModal = () => {
  emit('update:modelValue', false)
  error.value = ''
}

const handleSignIn = async () => {
  loading.value = true
  error.value = ''

  try {
    await authStore.signInWithGoogle()
    // Modal will close automatically when auth state changes
    closeModal()
  } catch (err: any) {
    error.value = err.message || 'Failed to sign in. Please try again.'
    loading.value = false
  }
}
</script>

<style scoped>
/* Modal Animation */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active > div:last-child,
.modal-leave-active > div:last-child {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div:last-child,
.modal-leave-to > div:last-child {
  transform: scale(0.9);
  opacity: 0;
}

.modal-enter-to > div:last-child,
.modal-leave-from > div:last-child {
  transform: scale(1);
  opacity: 1;
}

/* Animation Delays */
.delay-700 {
  animation-delay: 700ms;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.05);
  }
}

.animate-pulse {
  animation: pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
