<template>
  <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold mb-6">Profile</h1>

    <!-- User Info -->
    <div class="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
      <div class="px-4 py-5 sm:px-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900">User Information</h3>
      </div>
      <div class="border-t border-gray-200 px-4 py-5 sm:px-6">
        <dl class="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div class="sm:col-span-1">
            <dt class="text-sm font-medium text-gray-500">Email</dt>
            <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.email }}</dd>
          </div>
          <div class="sm:col-span-1">
            <dt class="text-sm font-medium text-gray-500">User ID</dt>
            <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.id }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- Custom Topics -->
    <div class="bg-white shadow overflow-hidden sm:rounded-lg">
      <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
        <h3 class="text-lg leading-6 font-medium text-gray-900">My Custom Topics</h3>
        <button
          @click="showAddModal = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Topic
        </button>
      </div>
      <div class="border-t border-gray-200">
        <ul class="divide-y divide-gray-200">
          <li v-for="topic in customTopics" :key="topic.id" class="px-4 py-4 sm:px-6">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <h4 class="text-sm font-medium text-gray-900">{{ topic.name }}</h4>
                <p class="text-sm text-gray-500">{{ topic.description || 'No description' }}</p>
                <div class="mt-2 flex flex-wrap gap-1">
                  <span
                    v-for="keyword in topic.keywords"
                    :key="keyword"
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
              <div class="ml-4 flex space-x-2">
                <button
                  @click="editTopic(topic)"
                  class="text-blue-600 hover:text-blue-900"
                >
                  Edit
                </button>
                <button
                  @click="deleteTopic(topic.id)"
                  class="text-red-600 hover:text-red-900"
                >
                  Delete
                </button>
              </div>
            </div>
          </li>
          <li v-if="customTopics.length === 0" class="px-4 py-4 sm:px-6 text-center text-gray-500">
            No custom topics yet. Click "Add Topic" to create one.
          </li>
        </ul>
      </div>
    </div>

    <!-- Add/Edit Topic Modal -->
    <div v-if="showAddModal || editingTopic" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-medium mb-4">{{ editingTopic ? 'Edit Topic' : 'Add Topic' }}</h3>
        <form @submit.prevent="saveTopic">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Name</label>
              <input
                v-model="topicForm.name"
                type="text"
                required
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                v-model="topicForm.description"
                rows="3"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Keywords (comma-separated)</label>
              <input
                v-model="keywordsInput"
                type="text"
                placeholder="machine learning, neural networks"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const authStore = useAuthStore()
const topics = ref<any[]>([])
const showAddModal = ref(false)
const editingTopic = ref<any>(null)
const topicForm = ref({ name: '', description: '', keywords: [] })
const keywordsInput = ref('')

const customTopics = computed(() =>
  topics.value.filter(t => !t.is_system)
)

async function loadTopics() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/topics`)
    topics.value = response.data
  } catch (error) {
    console.error('Failed to load topics:', error)
  }
}

async function saveTopic() {
  const keywords = keywordsInput.value.split(',').map(k => k.trim()).filter(Boolean)
  const data = { ...topicForm.value, keywords }

  try {
    if (editingTopic.value) {
      await axios.put(
        `${import.meta.env.VITE_API_URL}/api/v1/topics/${editingTopic.value.id}`,
        data
      )
    } else {
      await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/topics`, data)
    }
    closeModal()
    loadTopics()
  } catch (error: any) {
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
