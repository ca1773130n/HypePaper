<template>
  <!-- Mobile Navigation Button -->
  <button
    @click="toggleMenu"
    class="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-purple-500/50 transition-all"
    aria-label="Toggle navigation menu"
  >
    <svg
      class="w-6 h-6 text-gray-200"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M4 6h16M4 12h16M4 18h16"
      />
    </svg>
  </button>

  <!-- Mobile Navigation Drawer -->
  <Transition name="slide">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50"
      @click.self="closeMenu"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-sm"
        @click="closeMenu"
      ></div>

      <!-- Drawer -->
      <div
        class="absolute top-0 right-0 h-full w-20 bg-[#0A0F1E]/95 backdrop-blur-xl border-l border-white/10 shadow-2xl"
        @click.stop
      >
        <!-- Header with close button -->
        <div class="flex items-center justify-center p-4 border-b border-white/5">
          <button
            @click="closeMenu"
            class="p-2 rounded-lg hover:bg-white/10 transition-all"
            aria-label="Close menu"
          >
            <svg
              class="w-5 h-5 text-gray-400"
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
        </div>

        <!-- Menu Items -->
        <nav class="flex flex-col items-center py-6 space-y-6">
          <!-- Authenticated Menu Items -->
          <template v-if="authStore.isAuthenticated">
            <button
              @click="handleNavigation('crawler')"
              class="group flex flex-col items-center justify-center w-12 h-12 rounded-xl hover:bg-white/10 transition-all"
              title="Crawl Papers"
            >
              <svg class="w-6 h-6 text-gray-400 group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>

            <button
              @click="handleSync"
              :disabled="isSyncing"
              class="group flex flex-col items-center justify-center w-12 h-12 rounded-xl hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title="Sync Database"
            >
              <svg
                v-if="isSyncing"
                class="animate-spin w-6 h-6 text-green-400"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-6 h-6 text-gray-400 group-hover:text-green-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>

            <button
              @click="handleNavigation('profile')"
              class="group flex flex-col items-center justify-center w-12 h-12 rounded-xl hover:bg-white/10 transition-all"
              title="Profile"
            >
              <svg class="w-6 h-6 text-gray-400 group-hover:text-purple-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </button>

            <div class="w-full px-4 py-3 border-t border-white/5"></div>

            <button
              @click="handleSignOut"
              class="group flex flex-col items-center justify-center w-12 h-12 rounded-xl hover:bg-white/10 transition-all"
              title="Sign Out"
            >
              <svg class="w-6 h-6 text-gray-400 group-hover:text-red-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </template>

          <!-- Non-authenticated Menu Items -->
          <template v-else>
            <button
              @click="handleNavigation('login')"
              class="group flex flex-col items-center justify-center w-12 h-12 rounded-xl hover:bg-gradient-to-br hover:from-purple-500/20 hover:to-pink-500/20 transition-all"
              title="Sign In"
            >
              <svg class="w-6 h-6 text-gray-400 group-hover:text-purple-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
            </button>
          </template>
        </nav>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

interface Props {
  paperCount?: number
  isSyncing?: boolean
}

interface Emits {
  (e: 'sync'): void
}

const props = withDefaults(defineProps<Props>(), {
  paperCount: 0,
  isSyncing: false,
})

const emit = defineEmits<Emits>()

const router = useRouter()
const authStore = useAuthStore()
const isOpen = ref(false)

const toggleMenu = () => {
  isOpen.value = !isOpen.value
  // Prevent body scroll when menu is open
  if (isOpen.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}

const closeMenu = () => {
  isOpen.value = false
  document.body.style.overflow = ''
}

const handleNavigation = (route: string) => {
  closeMenu()
  router.push(`/${route}`)
}

const handleSync = () => {
  emit('sync')
}

const handleSignOut = async () => {
  closeMenu()
  await authStore.signOut()
}
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: opacity 0.3s ease;
}

.slide-enter-active > div:last-child,
.slide-leave-active > div:last-child {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-from > div:last-child,
.slide-leave-to > div:last-child {
  transform: translateX(100%);
}

.slide-enter-to > div:last-child,
.slide-leave-from > div:last-child {
  transform: translateX(0);
}
</style>
