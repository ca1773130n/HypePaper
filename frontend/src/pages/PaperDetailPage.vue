<template>
  <div v-if="paper" class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <div class="mb-6">
      <h1 class="text-3xl font-bold mb-2">{{ paper.title }}</h1>
      <p class="text-gray-600">{{ paper.authors }}</p>
      <p class="text-sm text-gray-500">Published: {{ formatDate(paper.published_date) }}</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="md:col-span-2 space-y-6">
        <!-- Abstract -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Abstract</h2>
          <p class="text-gray-700">{{ paper.abstract }}</p>
        </div>

        <!-- Star History Chart -->
        <div v-if="starHistory.length > 0" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Star History</h2>
          <div class="h-64">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </div>

        <!-- References -->
        <div v-if="references.length > 0" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Citation Graph</h2>
          <div class="space-y-2">
            <div v-for="ref in references" :key="ref.paper_id" class="border-l-4 pl-4" :class="ref.relationship === 'cites' ? 'border-blue-500' : 'border-green-500'">
              <router-link :to="`/papers/${ref.paper_id}`" class="text-blue-600 hover:underline">
                {{ ref.title }}
              </router-link>
              <p class="text-sm text-gray-600">{{ ref.authors.join(', ') }} ({{ ref.year }})</p>
              <span class="text-xs text-gray-500">{{ ref.relationship === 'cites' ? 'Referenced by this paper' : 'Cites this paper' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Metrics -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Metrics</h2>
          <dl class="space-y-2">
            <div>
              <dt class="text-sm text-gray-500">Citations</dt>
              <dd class="text-2xl font-bold">{{ paper.citations || 0 }}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">GitHub Stars</dt>
              <dd class="text-2xl font-bold">{{ paper.github_stars || 0 }}</dd>
            </div>
          </dl>
        </div>

        <!-- Hype Scores -->
        <div v-if="hypeScores" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Hype Scores</h2>
          <dl class="space-y-2">
            <div>
              <dt class="text-sm text-gray-500">Average</dt>
              <dd class="text-xl font-bold">{{ hypeScores.average_hype }}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">Weekly Growth</dt>
              <dd class="text-xl font-bold">{{ hypeScores.weekly_hype }}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">Monthly Growth</dt>
              <dd class="text-xl font-bold">{{ hypeScores.monthly_hype }}</dd>
            </div>
          </dl>
          <p class="text-xs text-gray-500 mt-4">{{ hypeScores.formula_explanation }}</p>
        </div>

        <!-- Links -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Links</h2>
          <div class="space-y-2">
            <a v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank" class="block text-blue-600 hover:underline">
              View PDF
            </a>
            <a :href="`${apiUrl}/api/v1/papers/${paper.id}/download-pdf`" target="_blank" class="block text-blue-600 hover:underline">
              Download PDF
            </a>
            <a v-if="paper.github_url" :href="paper.github_url" target="_blank" class="block text-blue-600 hover:underline">
              GitHub Repository
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const apiUrl = import.meta.env.VITE_API_URL
const paper = ref<any>(null)
const starHistory = ref<any[]>([])
const hypeScores = ref<any>(null)
const references = ref<any[]>([])

async function loadPaper() {
  const paperId = route.params.id
  try {
    const [paperRes, historyRes, scoresRes, refsRes] = await Promise.all([
      axios.get(`${apiUrl}/api/v1/papers/${paperId}`),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/star-history`).catch(() => ({ data: [] })),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/hype-scores`).catch(() => ({ data: null })),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/references`).catch(() => ({ data: [] }))
    ])

    paper.value = paperRes.data
    starHistory.value = historyRes.data
    hypeScores.value = scoresRes.data
    references.value = refsRes.data
  } catch (error) {
    console.error('Failed to load paper:', error)
  }
}

function formatDate(isoString: string) {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleDateString()
}

onMounted(() => {
  loadPaper()
})
</script>
