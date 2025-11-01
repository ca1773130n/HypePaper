<template>
  <div class="min-h-screen bg-[#0A0F1E]">
    <!-- Header -->
    <header class="border-b border-white/10 backdrop-blur-xl bg-white/5">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent cursor-pointer" @click="navigateToHome">
              HypePaper
            </h1>
            <p class="mt-2 text-gray-400 text-sm font-light tracking-wide">Discover what's trending in research</p>
          </div>
          <div class="flex items-center gap-3">
            <!-- Desktop Buttons (hidden on mobile) -->
            <button
              @click="navigateToHome"
              class="hidden md:block px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-purple-500/50 transition-all text-gray-200 text-sm font-medium"
            >
              Home
            </button>
            <button
              @click="handleSignOut"
              class="hidden md:block px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-red-500/50 transition-all text-gray-400 hover:text-red-300 text-sm"
            >
              Sign Out
            </button>

            <!-- Profile Icon (visible on all screen sizes) -->
            <ProfileIcon />
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold mb-6 text-white">Profile</h1>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p class="mt-4 text-gray-400">Loading profile...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 mb-6">
        <p class="text-red-300">{{ error }}</p>
        <button @click="loadProfile" class="mt-2 text-sm text-purple-400 hover:text-purple-300">
          Try again
        </button>
      </div>

      <div v-else class="space-y-6">
        <!-- User Info & Stats in Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- User Info Card -->
          <div class="lg:col-span-2 bg-white/5 backdrop-blur-xl border border-white/10 shadow overflow-hidden sm:rounded-lg">
            <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
              <h3 class="text-lg leading-6 font-medium text-white">User Information</h3>
              <button
                @click="showEditProfile = true"
                class="px-3 py-1 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-lg hover:bg-purple-500/30 transition-all text-sm"
              >
                Edit Profile
              </button>
            </div>
            <div class="border-t border-white/10 px-4 py-5 sm:px-6">
              <dl class="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                <div class="sm:col-span-1">
                  <dt class="text-sm font-medium text-gray-400">Email</dt>
                  <dd class="mt-1 text-sm text-gray-200">{{ profile?.email }}</dd>
                </div>
                <div class="sm:col-span-1">
                  <dt class="text-sm font-medium text-gray-400">Display Name</dt>
                  <dd class="mt-1 text-sm text-gray-200">{{ profile?.display_name || 'Not set' }}</dd>
                </div>
                <div class="sm:col-span-1">
                  <dt class="text-sm font-medium text-gray-400">Member Since</dt>
                  <dd class="mt-1 text-sm text-gray-200">{{ formatDate(stats?.member_since) }}</dd>
                </div>
                <div class="sm:col-span-1">
                  <dt class="text-sm font-medium text-gray-400">Last Login</dt>
                  <dd class="mt-1 text-sm text-gray-200">{{ formatDate(stats?.last_login) }}</dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Statistics Card -->
          <div class="bg-white/5 backdrop-blur-xl border border-white/10 shadow overflow-hidden sm:rounded-lg">
            <div class="px-4 py-5 sm:px-6">
              <h3 class="text-lg leading-6 font-medium text-white">Activity Stats</h3>
            </div>
            <div class="border-t border-white/10 px-4 py-5 sm:px-6">
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-400">Total Jobs</span>
                  <span class="text-lg font-bold text-blue-300">{{ stats?.total_crawler_jobs || 0 }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-400">Active Jobs</span>
                  <span class="text-lg font-bold text-green-300">{{ stats?.active_crawler_jobs || 0 }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-400">Custom Topics</span>
                  <span class="text-lg font-bold text-purple-300">{{ stats?.custom_topics || 0 }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-400">Completed</span>
                  <span class="text-lg font-bold text-pink-300">{{ stats?.inactive_crawler_jobs || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Crawler Jobs Card -->
        <div class="bg-white/5 backdrop-blur-xl border border-white/10 shadow overflow-hidden sm:rounded-lg">
          <div class="px-4 py-5 sm:px-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <h3 class="text-lg leading-6 font-medium text-white">My Crawler Jobs</h3>
            <div class="flex gap-2">
              <button
                @click="jobFilter = null"
                :class="[
                  'px-3 py-1 rounded-lg text-sm transition-all',
                  jobFilter === null
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                ]"
              >
                All ({{ jobs.length }})
              </button>
              <button
                @click="jobFilter = 'processing'"
                :class="[
                  'px-3 py-1 rounded-lg text-sm transition-all',
                  jobFilter === 'processing'
                    ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                    : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                ]"
              >
                Active ({{ jobs.filter(j => j.status === 'processing').length }})
              </button>
              <button
                @click="jobFilter = 'completed'"
                :class="[
                  'px-3 py-1 rounded-lg text-sm transition-all',
                  jobFilter === 'completed'
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                ]"
              >
                Completed ({{ jobs.filter(j => j.status === 'completed').length }})
              </button>
            </div>
          </div>
          <div class="border-t border-white/10">
            <ul class="divide-y divide-white/10">
              <li v-for="job in filteredJobs" :key="job.id" class="px-4 py-4 sm:px-6 hover:bg-white/5 transition-all">
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <h4 class="text-sm font-medium text-white">{{ job.job_id }}</h4>
                      <span
                        :class="[
                          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                          job.status === 'processing'
                            ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                            : job.status === 'completed'
                            ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                            : 'bg-red-500/20 text-red-300 border border-red-500/30'
                        ]"
                      >
                        {{ job.status }}
                      </span>
                    </div>
                    <div class="mt-1 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-gray-400">
                      <span>Source: <span class="text-gray-300">{{ job.source_type }}</span></span>
                      <span>Papers: <span class="text-gray-300">{{ job.papers_crawled }}</span></span>
                      <span>Refs: <span class="text-gray-300">{{ job.references_crawled }}</span></span>
                      <span>Started: <span class="text-gray-300">{{ formatDateShort(job.started_at) }}</span></span>
                    </div>
                    <div v-if="job.keywords" class="mt-2 text-xs text-gray-400">
                      Keywords: <span class="text-purple-300">{{ job.keywords }}</span>
                    </div>
                  </div>
                </div>
              </li>
              <li v-if="filteredJobs.length === 0" class="px-4 py-8 sm:px-6 text-center text-gray-400">
                No crawler jobs found{{ jobFilter ? ` with status "${jobFilter}"` : '' }}.
              </li>
            </ul>
          </div>
        </div>

        <!-- Custom Topics Card -->
        <div class="bg-white/5 backdrop-blur-xl border border-white/10 shadow overflow-hidden sm:rounded-lg">
          <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
            <h3 class="text-lg leading-6 font-medium text-white">My Custom Topics ({{ customTopics.length }})</h3>
            <button
              @click="showAddModal = true"
              class="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:from-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/50 transition-all text-sm"
            >
              + Add Topic
            </button>
          </div>
          <div class="border-t border-white/10">
            <ul class="divide-y divide-white/10">
              <li v-for="topic in customTopics" :key="topic.id" class="px-4 py-4 sm:px-6 hover:bg-white/5 transition-all">
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <h4 class="text-sm font-medium text-white">{{ topic.name }}</h4>
                    <p class="text-sm text-gray-400 mt-1">{{ topic.description || 'No description' }}</p>
                    <div class="mt-2 flex flex-wrap gap-1">
                      <span
                        v-for="keyword in topic.keywords"
                        :key="keyword"
                        class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      >
                        {{ keyword }}
                      </span>
                    </div>
                  </div>
                  <div class="ml-4 flex space-x-2">
                    <button
                      @click="editTopic(topic)"
                      class="text-blue-400 hover:text-blue-300 text-sm"
                    >
                      Edit
                    </button>
                    <button
                      @click="deleteTopic(topic.id)"
                      class="text-red-400 hover:text-red-300 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </li>
              <li v-if="customTopics.length === 0" class="px-4 py-8 sm:px-6 text-center text-gray-400">
                No custom topics yet. Click "Add Topic" to create one.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Profile Modal -->
    <div v-if="showEditProfile" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showEditProfile = false">
      <div class="bg-gray-800 rounded-xl p-6 max-w-md w-full border border-white/20 shadow-2xl mx-4">
        <h3 class="text-lg font-medium mb-4 text-white">Edit Profile</h3>
        <form @submit.prevent="saveProfile">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Display Name</label>
              <input
                v-model="profileForm.display_name"
                type="text"
                class="w-full rounded-lg bg-white/5 border border-white/10 text-white shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 px-3 py-2"
                placeholder="Your display name"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Avatar URL</label>
              <input
                v-model="profileForm.avatar_url"
                type="url"
                class="w-full rounded-lg bg-white/5 border border-white/10 text-white shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 px-3 py-2"
                placeholder="https://example.com/avatar.jpg"
              />
            </div>
          </div>
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="showEditProfile = false"
              class="px-4 py-2 border border-white/10 rounded-lg text-gray-300 hover:bg-white/5 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg shadow-purple-500/30"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add/Edit Topic Modal -->
    <div v-if="showAddModal || editingTopic" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" @click.self="closeModal">
      <div class="bg-gray-800 rounded-xl p-6 max-w-md w-full border border-white/20 shadow-2xl mx-4">
        <h3 class="text-lg font-medium mb-4 text-white">{{ editingTopic ? 'Edit Topic' : 'Add New Topic' }}</h3>
        <form @submit.prevent="saveTopic">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Name</label>
              <input
                v-model="topicForm.name"
                type="text"
                required
                class="w-full rounded-lg bg-white/5 border border-white/10 text-white shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 px-3 py-2"
                placeholder="e.g., reinforcement-learning"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Description</label>
              <textarea
                v-model="topicForm.description"
                rows="3"
                class="w-full rounded-lg bg-white/5 border border-white/10 text-white shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 px-3 py-2"
                placeholder="Describe this topic..."
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Keywords (comma-separated)</label>
              <input
                v-model="keywordsInput"
                type="text"
                placeholder="rl, agent, policy gradient"
                class="w-full rounded-lg bg-white/5 border border-white/10 text-white shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 px-3 py-2 placeholder-gray-500"
              />
            </div>
          </div>
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 border border-white/10 rounded-lg text-gray-300 hover:bg-white/5 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg shadow-purple-500/30"
            >
              {{ editingTopic ? 'Update' : 'Create' }} Topic
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api, profileApi, type UserProfile, type UserStats, type CrawlerJob, type Topic } from '@/services/api'
import ProfileIcon from '@/components/ProfileIcon.vue'

const router = useRouter()
const authStore = useAuthStore()

// State
const loading = ref(true)
const error = ref<string | null>(null)
const profile = ref<UserProfile | null>(null)
const stats = ref<UserStats | null>(null)
const jobs = ref<CrawlerJob[]>([])
const customTopics = ref<Topic[]>([])
const jobFilter = ref<string | null>(null)

// Modals
const showEditProfile = ref(false)
const showAddModal = ref(false)
const editingTopic = ref<any>(null)

// Forms
const profileForm = ref({ display_name: '', avatar_url: '' })
const topicForm = ref({ name: '', description: '', keywords: [] })
const keywordsInput = ref('')

// Computed
const filteredJobs = computed(() => {
  if (!jobFilter.value) return jobs.value
  return jobs.value.filter(job => job.status === jobFilter.value)
})

// Methods
const navigateToHome = () => {
  router.push('/')
}

const handleSignOut = async () => {
  await authStore.signOut()
  router.push('/')
}

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDateShort = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  })
}

async function loadProfile() {
  try {
    loading.value = true
    error.value = null

    console.log('[Profile] Loading profile data...')
    const [profileRes, statsRes, jobsRes, topicsRes] = await Promise.all([
      profileApi.getProfile(),
      profileApi.getStats(),
      profileApi.getCrawlerJobs(),
      profileApi.getCustomTopics()
    ])

    profile.value = profileRes.data
    stats.value = statsRes.data
    jobs.value = jobsRes.data
    customTopics.value = topicsRes.data

    console.log('[Profile] Loaded:', { profile: profile.value, stats: stats.value, jobs: jobs.value.length, topics: customTopics.value.length })

    // Initialize profile form
    profileForm.value = {
      display_name: profile.value.display_name || '',
      avatar_url: profile.value.avatar_url || ''
    }
  } catch (err: any) {
    console.error('[Profile] Failed to load profile:', err)
    error.value = err.response?.data?.detail || 'Failed to load profile. Please try again.'
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  try {
    console.log('[Profile] Updating profile:', profileForm.value)
    const response = await profileApi.updateProfile(profileForm.value)
    profile.value = response.data
    showEditProfile.value = false
    console.log('[Profile] Profile updated successfully')
  } catch (err: any) {
    console.error('[Profile] Failed to update profile:', err)
    alert(err.response?.data?.detail || 'Failed to update profile')
  }
}

async function saveTopic() {
  const keywords = keywordsInput.value.split(',').map(k => k.trim()).filter(Boolean)
  const data = {
    name: topicForm.value.name,
    description: topicForm.value.description || null,
    keywords
  }

  try {
    console.log('[Profile] Saving topic:', data)
    if (editingTopic.value) {
      await api.put(`/api/v1/topics/${editingTopic.value.id}`, data)
    } else {
      await api.post('/api/v1/topics', data)
    }
    closeModal()
    await loadProfile()
  } catch (error: any) {
    console.error('[Profile] Failed to save topic:', error)
    alert(error.response?.data?.detail || 'Failed to save topic')
  }
}

function editTopic(topic: any) {
  editingTopic.value = topic
  topicForm.value = {
    name: topic.name,
    description: topic.description || '',
    keywords: topic.keywords || []
  }
  keywordsInput.value = (topic.keywords || []).join(', ')
}

async function deleteTopic(id: string) {
  if (!confirm('Are you sure you want to delete this topic?')) return

  try {
    console.log('[Profile] Deleting topic:', id)
    await api.delete(`/api/v1/topics/${id}`)
    await loadProfile()
  } catch (error: any) {
    console.error('[Profile] Failed to delete topic:', error)
    alert(error.response?.data?.detail || 'Failed to delete topic')
  }
}

function closeModal() {
  showAddModal.value = false
  editingTopic.value = null
  topicForm.value = { name: '', description: '', keywords: [] }
  keywordsInput.value = ''
}

onMounted(() => {
  loadProfile()
})
</script>
