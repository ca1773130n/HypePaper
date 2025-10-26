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
            <button
              @click="navigateToHome"
              class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-purple-500/50 transition-all text-gray-200 text-sm font-medium"
            >
              Home
            </button>
            <button
              @click="handleSignOut"
              class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-red-500/50 transition-all text-gray-400 hover:text-red-300 text-sm"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold mb-6 text-white">Profile</h1>

    <!-- User Info -->
    <div class="bg-white/5 backdrop-blur-xl border border-white/10 shadow overflow-hidden sm:rounded-lg mb-6">
      <div class="px-4 py-5 sm:px-6">
        <h3 class="text-lg leading-6 font-medium text-white">User Information</h3>
      </div>
      <div class="border-t border-white/10 px-4 py-5 sm:px-6">
        <dl class="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div class="sm:col-span-1">
            <dt class="text-sm font-medium text-gray-400">Email</dt>
            <dd class="mt-1 text-sm text-gray-200">{{ authStore.user?.email }}</dd>
          </div>
          <div class="sm:col-span-1">
            <dt class="text-sm font-medium text-gray-400">User ID</dt>
            <dd class="mt-1 text-sm text-gray-200">{{ authStore.user?.id }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- Custom Topics -->
    <div class="bg-white/5 backdrop-blur-xl border border-white/10 shadow overflow-hidden sm:rounded-lg">
      <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
        <h3 class="text-lg leading-6 font-medium text-white">My Custom Topics</h3>
        <button
          @click="showAddModal = true"
          class="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:from-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/50 transition-all"
        >
          Add Topic
        </button>
      </div>
      <div class="border-t border-white/10">
        <ul class="divide-y divide-white/10">
          <li v-for="topic in customTopics" :key="topic.id" class="px-4 py-4 sm:px-6">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <h4 class="text-sm font-medium text-white">{{ topic.name }}</h4>
                <p class="text-sm text-gray-400">{{ topic.description || 'No description' }}</p>
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
                  class="text-blue-400 hover:text-blue-300"
                >
                  Edit
                </button>
                <button
                  @click="deleteTopic(topic.id)"
                  class="text-red-400 hover:text-red-300"
                >
                  Delete
                </button>
              </div>
            </div>
          </li>
          <li v-if="customTopics.length === 0" class="px-4 py-4 sm:px-6 text-center text-gray-400">
            No custom topics yet. Click "Add Topic" to create one.
          </li>
        </ul>
      </div>
    </div>
    </div>
  </div>

    <!-- Add/Edit Topic Modal -->
    <div v-if="showAddModal || editingTopic" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-medium mb-4 text-gray-900">{{ editingTopic ? 'Edit Topic' : 'Add Topic' }}</h3>
        <form @submit.prevent="saveTopic">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Name</label>
              <input
                v-model="topicForm.name"
                type="text"
                required
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-gray-900"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                v-model="topicForm.description"
                rows="3"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-gray-900"
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Keywords (comma-separated)</label>
              <input
                v-model="keywordsInput"
                type="text"
                placeholder="machine learning, neural networks"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
              />
            </div>
          </div>
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
const topics = ref<any[]>([])
const showAddModal = ref(false)
const editingTopic = ref<any>(null)
const topicForm = ref({ name: '', description: '', keywords: [] })
const keywordsInput = ref('')

const navigateToHome = () => {
  router.push('/')
}

const handleSignOut = async () => {
  await authStore.signOut()
  router.push('/')
}

const customTopics = computed(() =>
  topics.value.filter(t => !t.is_system)
)

async function loadTopics() {
  try {
    console.log('[DEBUG] Loading topics...')
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/topics`)
    console.log('[DEBUG] Topics loaded:', response.data)
    topics.value = response.data
  } catch (error) {
    console.error('[DEBUG] Failed to load topics:', error)
    console.error('[DEBUG] Error response:', error.response?.data)
    console.error('[DEBUG] Error status:', error.response?.status)
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
    console.log('[DEBUG] Saving topic:', data)

    if (editingTopic.value) {
      await axios.put(
        `${import.meta.env.VITE_API_URL}/api/v1/topics/${editingTopic.value.id}`,
        data
      )
    } else {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/topics`, data)
      console.log('[DEBUG] Topic created:', response.data)
    }
    closeModal()
    loadTopics()
  } catch (error: any) {
    console.error('[DEBUG] Failed to save topic:', error)
    console.error('[DEBUG] Error response:', error.response?.data)
    console.error('[DEBUG] Error status:', error.response?.status)
    console.error('[DEBUG] Error headers:', error.response?.headers)
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
    await axios.delete(`${import.meta.env.VITE_API_URL}/api/v1/topics/${id}`)
    loadTopics()
  } catch (error: any) {
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
  loadTopics()
})
</script>
