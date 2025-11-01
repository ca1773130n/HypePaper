<template>
  <div class="min-h-screen bg-[#0A0F1E]">
    <!-- Animated Background -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-700"></div>
      <div class="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
    </div>

    <!-- Header -->
    <header class="relative border-b border-white/10 backdrop-blur-xl bg-white/5">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              HypePaper
            </h1>
            <p class="mt-2 text-gray-400 text-sm font-light tracking-wide">Discover what's trending in research</p>
          </div>
          <div class="flex items-center gap-3">
            <!-- Desktop Auth Buttons (hidden on mobile) -->
            <div v-if="authStore.isAuthenticated" class="hidden md:flex items-center gap-3">
              <button
                @click="navigateToCrawler"
                class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-blue-500/50 transition-all text-gray-200 text-sm font-medium"
              >
                Crawl Papers
              </button>
              <button
                @click="syncDatabase"
                :disabled="isSyncing"
                class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-green-500/50 transition-all text-gray-200 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span v-if="isSyncing" class="flex items-center gap-2">
                  <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Syncing...
                </span>
                <span v-else>Sync DB</span>
              </button>
              <button
                @click="navigateToProfile"
                class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-purple-500/50 transition-all text-gray-200 text-sm font-medium"
              >
                Profile
              </button>
              <button
                @click="handleSignOut"
                class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-red-500/50 transition-all text-gray-400 hover:text-red-300 text-sm"
              >
                Sign Out
              </button>
            </div>
            <button
              v-else
              @click="navigateToLogin"
              class="hidden md:block px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white text-sm font-medium shadow-lg shadow-purple-500/50 transition-all"
            >
              Sign In
            </button>

            <!-- Profile Icon (visible on all screen sizes) -->
            <ProfileIcon @open-sign-in="showSignInModal = true" />
          </div>
        </div>
      </div>
    </header>

    <!-- Sign In Modal -->
    <SignInModal v-model="showSignInModal" />

    <!-- Main Content -->
    <main class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- Filters Section -->
      <div class="mb-12 space-y-6">
        <!-- Topic Selector -->
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <label class="text-sm font-medium text-gray-300 min-w-fit">
            Topic
          </label>
          <div ref="topicDropdownRef" class="relative w-full sm:w-96">
            <button
              @click="topicDropdownOpen = !topicDropdownOpen"
              class="w-full inline-flex items-center justify-between rounded-xl bg-white/5 backdrop-blur-xl px-5 py-3.5 text-sm border border-white/10 hover:border-white/20 hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
            >
              <span class="text-gray-200">
                {{ selectedTopicLabels }}
              </span>
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <!-- Checkbox Dropdown -->
            <div
              v-if="topicDropdownOpen"
              class="absolute top-full mt-2 w-full bg-[#1A1F35] backdrop-blur-2xl rounded-xl shadow-2xl border border-white/10 overflow-hidden z-50 max-h-96 overflow-y-auto"
              @click.stop
            >
              <!-- All Topics -->
              <label
                class="flex items-center justify-between px-5 py-3 hover:bg-white/10 cursor-pointer transition-colors border-b border-white/10"
              >
                <span class="text-sm text-gray-200 font-medium">All Topics</span>
                <input
                  type="checkbox"
                  :checked="isAllTopicsSelected"
                  @change="toggleAllTopics"
                  class="w-4 h-4 rounded border-white/20 bg-white/5 text-purple-500 focus:ring-2 focus:ring-purple-500/50"
                />
              </label>

              <!-- User Topics -->
              <label
                v-for="topic in userTopics"
                :key="topic.id"
                :class="[
                  'flex items-center justify-between px-5 py-3 hover:bg-white/10 cursor-pointer transition-colors',
                  isAllTopicsSelected ? 'opacity-40' : ''
                ]"
              >
                <span class="text-sm text-gray-200">{{ topic.name }}</span>
                <input
                  type="checkbox"
                  :checked="selectedTopics.includes(topic.id)"
                  @change="toggleTopic(topic.id)"
                  :disabled="isAllTopicsSelected"
                  class="w-4 h-4 rounded border-white/20 bg-white/5 text-purple-500 focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </label>
            </div>
          </div>
        </div>

        <!-- Sort Controls -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <label class="text-sm font-medium text-gray-300 min-w-fit">Sort by</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="sort in sortOptions"
              :key="sort.value"
              @click="selectedSort = sort.value"
              :class="[
                'group relative px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                selectedSort === sort.value
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/50'
                  : 'bg-white/5 text-gray-300 border border-white/10 hover:bg-white/10 hover:border-white/20'
              ]"
            >
              <span class="relative z-10">{{ sort.label }}</span>
              <div v-if="selectedSort === sort.value" class="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl blur opacity-50"></div>
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col justify-center items-center py-24">
        <div class="relative">
          <div class="w-16 h-16 border-4 border-purple-500/20 rounded-full"></div>
          <div class="w-16 h-16 border-4 border-purple-500 rounded-full animate-spin border-t-transparent absolute top-0"></div>
        </div>
        <p class="mt-4 text-gray-400 text-sm">Loading papers...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-500/10 backdrop-blur-xl border border-red-500/20 rounded-2xl p-6 text-red-300">
        <div class="flex items-start gap-3">
          <svg class="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>{{ error }}</p>
        </div>
      </div>

      <!-- Papers Grid -->
      <div v-else-if="papers.length > 0" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="paper in papers"
          :key="paper.id"
          @click="navigateToPaper(paper.id)"
          class="group relative bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:bg-white/10 hover:border-purple-500/50 transition-all duration-300 cursor-pointer overflow-hidden"
        >
          <!-- Glow effect on hover -->
          <div class="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-pink-500/0 group-hover:from-purple-500/10 group-hover:to-pink-500/10 transition-all duration-300 rounded-2xl"></div>

          <div class="relative z-10">
            <!-- Category Badge -->
            <div class="flex items-center justify-between mb-3">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-300 border border-blue-500/30">
                {{ paper.venue || 'Research Paper' }}
              </span>
              <div v-if="paper.github_url" class="flex items-center gap-2 text-gray-400 group-hover:text-purple-300 transition-colors">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                <span v-if="paper.github_stars" class="flex items-center gap-1 text-xs font-medium">
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                  </svg>
                  {{ formatStarCount(paper.github_stars) }}
                </span>
              </div>
            </div>

            <!-- Title -->
            <h3 class="text-lg font-bold text-white mb-3 line-clamp-2 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-300 group-hover:to-purple-300 group-hover:bg-clip-text transition-all duration-300">
              {{ paper.title }}
            </h3>

            <!-- Authors -->
            <p class="text-sm text-gray-400 mb-3 line-clamp-2">
              {{ paper.authors.slice(0, 3).join(', ') }}
              <span v-if="paper.authors.length > 3" class="text-gray-500"> et al.</span>
            </p>

            <!-- Abstract -->
            <p class="text-sm text-gray-500 mb-4 line-clamp-3 leading-relaxed">
              {{ paper.abstract }}
            </p>

            <!-- Footer -->
            <div class="flex items-center justify-between pt-4 border-t border-white/5">
              <div class="flex items-center gap-4">
                <span class="text-xs text-gray-500 font-light">
                  {{ formatDate(paper.published_date) }}
                </span>
                <div @click.stop>
                  <VoteButton
                    :paper-id="paper.id"
                    :initial-vote-count="paper.vote_count || 0"
                    :initial-user-vote="null"
                  />
                </div>
              </div>
              <svg class="w-5 h-5 text-gray-600 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-24">
        <div class="relative inline-flex items-center justify-center w-24 h-24 mb-6">
          <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-full blur-xl"></div>
          <svg class="relative w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 class="text-xl font-semibold text-gray-300 mb-2">No papers found</h3>
        <p class="text-gray-500">Try selecting a different topic or check back later</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import {
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectIcon,
  SelectPortal,
  SelectContent,
  SelectViewport,
  SelectItem,
  SelectItemText,
  SelectItemIndicator,
} from 'reka-ui'
import { topicsApi, papersApi, type Topic, type Paper } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import VoteButton from '@/components/VoteButton.vue'
import ProfileIcon from '@/components/ProfileIcon.vue'
import SignInModal from '@/components/SignInModal.vue'

const router = useRouter()
const authStore = useAuthStore()

const topics = ref<Topic[]>([])
const userTopics = computed(() => topics.value.filter((t: any) => !t.is_system))
const papers = ref<Paper[]>([])
const selectedTopics = ref<string[]>([])
const previousSelectedTopics = ref<string[]>([])
const isAllTopicsSelected = ref(true)
const topicDropdownOpen = ref(false)
const topicDropdownRef = ref<HTMLElement | null>(null)
const selectedSort = ref<'hype_score' | 'recency' | 'stars' | 'citations'>('hype_score')
const loading = ref(false)
const error = ref('')
const isSyncing = ref(false)
const showSignInModal = ref(false)

const sortOptions = [
  { value: 'hype_score' as const, label: '🔥 Hype Score' },
  { value: 'recency' as const, label: '🆕 Recent' },
  { value: 'stars' as const, label: '⭐ Stars' },
  { value: 'citations' as const, label: '📚 Citations' },
]

const selectedTopicLabels = computed(() => {
  if (isAllTopicsSelected.value) {
    return 'All Topics'
  }
  if (selectedTopics.value.length === 0) {
    return 'Select Topics'
  }
  if (selectedTopics.value.length === 1) {
    const topic = userTopics.value.find((t: any) => t.id === selectedTopics.value[0])
    return topic?.name || 'Select Topics'
  }
  return `${selectedTopics.value.length} Topics Selected`
})

const toggleAllTopics = () => {
  if (isAllTopicsSelected.value) {
    // Unchecking "All Topics" - restore previous selection
    isAllTopicsSelected.value = false
    selectedTopics.value = [...previousSelectedTopics.value]
  } else {
    // Checking "All Topics" - save current selection and clear
    previousSelectedTopics.value = [...selectedTopics.value]
    isAllTopicsSelected.value = true
    selectedTopics.value = []
  }
}

const toggleTopic = (topicId: string) => {
  const index = selectedTopics.value.indexOf(topicId)
  if (index > -1) {
    selectedTopics.value.splice(index, 1)
  } else {
    selectedTopics.value.push(topicId)
  }
  // Update previous selection when manually selecting topics
  previousSelectedTopics.value = [...selectedTopics.value]
}

const fetchTopics = async () => {
  try {
    console.log('[HomePage] Fetching topics, authenticated:', authStore.isAuthenticated)
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/topics`)
    console.log('[HomePage] Topics received:', response.data)
    topics.value = response.data
    console.log('[HomePage] User topics filtered:', userTopics.value)
  } catch (err) {
    console.error('Failed to fetch topics:', err)
  }
}

const fetchPapers = async () => {
  loading.value = true
  error.value = ''
  try {
    // For now, if multiple topics selected, show all papers
    // TODO: Backend support for multiple topic filtering
    const topicId = isAllTopicsSelected.value || selectedTopics.value.length === 0
      ? undefined
      : selectedTopics.value.length === 1
        ? selectedTopics.value[0]
        : undefined

    // Only include topic_id in params if it's defined to avoid sending undefined
    const response = await papersApi.getAll({
      ...(topicId && { topic_id: topicId }),
      sort_by: selectedSort.value,
      limit: 100,
    })
    papers.value = response.data.papers
  } catch (err) {
    error.value = 'Failed to load papers. Please try again.'
    console.error('Failed to fetch papers:', err)
  } finally {
    loading.value = false
  }
}

const navigateToPaper = (id: string) => {
  router.push(`/papers/${id}`)
}

const navigateToLogin = () => {
  router.push('/login')
}

const navigateToProfile = () => {
  router.push('/profile')
}

const navigateToCrawler = () => {
  router.push('/crawler')
}

const syncDatabase = async () => {
  if (isSyncing.value) return

  if (!confirm('This will synchronize all papers with enrichment data (GitHub URLs, citations, authors). This may take several minutes. Continue?')) {
    return
  }

  isSyncing.value = true
  try {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const response = await axios.post(`${apiUrl}/api/v1/jobs/sync-database`)

    alert(`Sync started! ${response.data.results?.enriched_papers || 0} papers enriched, ${response.data.results?.authors_created || 0} authors created.`)

    // Refresh papers list
    await fetchPapers()
  } catch (err: any) {
    console.error('Sync failed:', err)
    alert(`Sync failed: ${err.response?.data?.detail || err.message}`)
  } finally {
    isSyncing.value = false
  }
}

const handleSignOut = async () => {
  await authStore.signOut()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatStarCount = (count: number): string => {
  if (count >= 1000000) {
    return (count / 1000000).toFixed(1).replace(/\.0$/, '') + 'M'
  }
  if (count >= 1000) {
    return (count / 1000).toFixed(1).replace(/\.0$/, '') + 'k'
  }
  return count.toString()
}

watch([selectedTopics, isAllTopicsSelected, selectedSort], () => {
  fetchPapers()
}, { deep: true })

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  if (topicDropdownRef.value && !topicDropdownRef.value.contains(event.target as Node)) {
    topicDropdownOpen.value = false
  }
}

onMounted(async () => {
  // Wait for auth session to be restored
  await authStore.fetchUser()

  // Now fetch topics and papers
  fetchTopics()
  fetchPapers()
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Refetch topics when navigating back to this page
watch(() => router.currentRoute.value.path, (newPath) => {
  if (newPath === '/') {
    fetchTopics()
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.1;
    transform: scale(1);
  }
  50% {
    opacity: 0.15;
    transform: scale(1.05);
  }
}

.animate-pulse {
  animation: pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.delay-700 {
  animation-delay: 700ms;
}

.delay-1000 {
  animation-delay: 1000ms;
}
</style>
