<template>
  <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold mb-6">Admin Dashboard</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- ArXiv Crawl -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">ArXiv Crawl</h2>
        <form @submit.prevent="crawlArxiv" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Query</label>
            <input
              v-model="arxivQuery"
              type="text"
              placeholder="diffusion models"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Limit</label>
            <input
              v-model.number="arxivLimit"
              type="number"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
          <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700">
            Start Crawl
          </button>
        </form>
      </div>

      <!-- Conference Crawl -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">Conference Crawl</h2>
        <form @submit.prevent="crawlConference" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Conference</label>
            <select v-model="conferenceName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
              <option value="CVPR">CVPR</option>
              <option value="ICLR">ICLR</option>
              <option value="NeurIPS">NeurIPS</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Year</label>
            <input
              v-model.number="conferenceYear"
              type="number"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
          <button type="submit" class="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700">
            Start Crawl
          </button>
        </form>
      </div>
    </div>

    <!-- Task Logs -->
    <div class="bg-white shadow rounded-lg p-6">
      <h2 class="text-xl font-semibold mb-4">Task Logs</h2>
      <button @click="loadTasks" class="mb-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
        Refresh
      </button>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Result</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="task in tasks" :key="task.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm">{{ task.task_type }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="statusClass(task.status)" class="px-2 py-1 text-xs rounded-full">
                  {{ task.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm">{{ formatDate(task.created_at) }}</td>
              <td class="px-6 py-4 text-sm">{{ task.result ? JSON.stringify(task.result).slice(0, 50) : '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const arxivQuery = ref('diffusion models')
const arxivLimit = ref(50)
const conferenceName = ref('CVPR')
const conferenceYear = ref(2024)
const tasks = ref<any[]>([])

async function crawlArxiv() {
  try {
    await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/admin/crawl/arxiv`, {
      query: arxivQuery.value,
      limit: arxivLimit.value
    })
    alert('ArXiv crawl started!')
    loadTasks()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Failed to start crawl')
  }
}

async function crawlConference() {
  try {
    await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/admin/crawl/conference`, {
      conference_name: conferenceName.value,
      conference_year: conferenceYear.value
    })
    alert('Conference crawl started!')
    loadTasks()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Failed to start crawl')
  }
}

async function loadTasks() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/admin/tasks?limit=20`)
    tasks.value = response.data
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
}

function statusClass(status: string) {
  return {
    'bg-yellow-100 text-yellow-800': status === 'pending',
    'bg-blue-100 text-blue-800': status === 'running',
    'bg-green-100 text-green-800': status === 'completed',
    'bg-red-100 text-red-800': status === 'failed'
  }
}

function formatDate(isoString: string) {
  return new Date(isoString).toLocaleString()
}

onMounted(() => {
  loadTasks()
})
</script>
