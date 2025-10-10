<template>
  <div v-if="paper" class="min-h-screen bg-[#0A0F1E]">
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
            <h1 class="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent cursor-pointer" @click="navigateToHome">
              HypePaper
            </h1>
            <p class="mt-2 text-gray-400 text-sm font-light tracking-wide">Discover what's trending in research</p>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="goBack"
              class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-purple-500/50 transition-all text-gray-200 text-sm font-medium"
            >
              ← Back
            </button>

            <!-- Auth Buttons -->
            <div v-if="authStore.isAuthenticated" class="flex items-center gap-3">
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
              class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white text-sm font-medium shadow-lg shadow-purple-500/50 transition-all"
            >
              Sign In
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="mb-6">
      <h1 class="text-3xl font-bold mb-3 text-white">{{ paper.title }}</h1>
      <div class="flex flex-wrap gap-2 mb-2">
        <span v-for="(author, index) in parseAuthors(paper.authors)" :key="index" class="px-3 py-1 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full text-sm text-gray-300">
          {{ author }}
        </span>
      </div>
      <p class="text-sm text-gray-500">Published: {{ formatDate(paper.published_date) }}</p>

      <!-- Icon Links Section -->
      <div class="flex flex-wrap gap-3 mt-4">
        <a v-if="paper.pdf_url || paper.arxiv_url" :href="paper.pdf_url || paper.arxiv_url" target="_blank"
           class="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 hover:border-red-500/50 rounded-lg text-red-400 hover:text-red-300 transition-all">
          <FileText :size="18" />
          <span class="text-sm font-medium">PDF</span>
        </a>
        <a v-if="paper.github_url" :href="paper.github_url" target="_blank"
           class="flex items-center gap-2 px-4 py-2 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 hover:border-purple-500/50 rounded-lg text-purple-400 hover:text-purple-300 transition-all">
          <Github :size="18" />
          <span class="text-sm font-medium">GitHub</span>
        </a>
        <a v-if="paper.project_page_url" :href="paper.project_page_url" target="_blank"
           class="flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 hover:border-blue-500/50 rounded-lg text-blue-400 hover:text-blue-300 transition-all">
          <Globe :size="18" />
          <span class="text-sm font-medium">Project</span>
        </a>
        <a v-if="paper.youtube_url" :href="paper.youtube_url" target="_blank"
           class="flex items-center gap-2 px-4 py-2 bg-red-600/10 hover:bg-red-600/20 border border-red-600/30 hover:border-red-600/50 rounded-lg text-red-500 hover:text-red-400 transition-all">
          <Youtube :size="18" />
          <span class="text-sm font-medium">Video</span>
        </a>
        <a v-if="paper.doi" :href="`https://doi.org/${paper.doi}`" target="_blank"
           class="flex items-center gap-2 px-4 py-2 bg-green-500/10 hover:bg-green-500/20 border border-green-500/30 hover:border-green-500/50 rounded-lg text-green-400 hover:text-green-300 transition-all">
          <Link2 :size="18" />
          <span class="text-sm font-medium">DOI</span>
        </a>
        <button @click="copyBibtex"
           class="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 hover:bg-yellow-500/20 border border-yellow-500/30 hover:border-yellow-500/50 rounded-lg text-yellow-400 hover:text-yellow-300 transition-all">
          <Copy :size="18" />
          <span class="text-sm font-medium">{{ bibtexCopied ? 'Copied!' : 'BibTeX' }}</span>
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="md:col-span-2 space-y-6">
        <!-- Abstract -->
        <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3 text-white">Abstract</h2>
          <p class="text-gray-300">{{ paper.abstract }}</p>
        </div>

        <!-- Star History Chart -->
        <div v-if="starHistory.length > 0" class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3 text-white">GitHub Stars History</h2>
          <div class="h-64">
            <canvas ref="starChartCanvas"></canvas>
          </div>
        </div>

        <!-- Citation History Chart -->
        <div v-if="citationHistory.length > 0" class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3 text-white">Citation History</h2>
          <div class="h-64">
            <canvas ref="citationChartCanvas"></canvas>
          </div>
        </div>

        <!-- References -->
        <div v-if="references.length > 0" class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3 text-white">Citation Graph</h2>
          <div class="space-y-2">
            <div v-for="ref in references" :key="ref.paper_id" class="border-l-4 pl-4" :class="ref.relationship === 'cites' ? 'border-blue-500' : 'border-green-500'">
              <router-link :to="`/papers/${ref.paper_id}`" class="text-blue-400 hover:text-blue-300">
                {{ ref.title }}
              </router-link>
              <p class="text-sm text-gray-400">{{ ref.authors.join(', ') }} ({{ ref.year }})</p>
              <span class="text-xs text-gray-500">{{ ref.relationship === 'cites' ? 'Referenced by this paper' : 'Cites this paper' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Metrics -->
        <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3 text-white">Metrics</h2>
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20 rounded-lg p-4">
              <dt class="text-xs text-blue-400 uppercase tracking-wider font-medium mb-1">Citations</dt>
              <dd class="text-3xl font-bold text-white">{{ paper.citations || 0 }}</dd>
            </div>
            <div class="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20 rounded-lg p-4">
              <dt class="text-xs text-purple-400 uppercase tracking-wider font-medium mb-1">GitHub Stars</dt>
              <dd class="text-3xl font-bold text-white">{{ paper.github_stars || 0 }}</dd>
            </div>
          </div>
        </div>

        <!-- Hype Scores -->
        <div v-if="hypeScores" class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3 text-white">Hype Scores</h2>
          <div class="space-y-3">
            <div class="bg-gradient-to-r from-pink-500/10 to-orange-500/10 border border-pink-500/20 rounded-lg p-3">
              <dt class="text-xs text-pink-400 uppercase tracking-wider font-medium mb-1">Average Hype</dt>
              <dd class="text-2xl font-bold text-white">{{ hypeScores.average_hype }}</dd>
            </div>
            <div class="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-lg p-3">
              <dt class="text-xs text-green-400 uppercase tracking-wider font-medium mb-1">Weekly Growth</dt>
              <dd class="text-2xl font-bold text-white">{{ hypeScores.weekly_hype }}</dd>
            </div>
            <div class="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-lg p-3">
              <dt class="text-xs text-cyan-400 uppercase tracking-wider font-medium mb-1">Monthly Growth</dt>
              <dd class="text-2xl font-bold text-white">{{ hypeScores.monthly_hype }}</dd>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-4">{{ hypeScores.formula_explanation }}</p>
        </div>

        <!-- Quick Links -->
        <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3 text-white">Quick Actions</h2>
          <div class="space-y-2">
            <a :href="`${apiUrl}/api/v1/papers/${paper.id}/download-pdf`" target="_blank"
               class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/10 to-pink-500/10 hover:from-purple-500/20 hover:to-pink-500/20 border border-purple-500/30 rounded-lg text-purple-300 hover:text-purple-200 transition-all">
              <Download :size="18" />
              <span class="text-sm">Download PDF</span>
            </a>
          </div>
        </div>
      </div>
    </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { FileText, Github, Globe, Youtube, Link2, Copy, Download } from 'lucide-vue-next'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const apiUrl = import.meta.env.VITE_API_URL
const paper = ref<any>(null)
const starHistory = ref<any[]>([])
const citationHistory = ref<any[]>([])
const hypeScores = ref<any>(null)
const references = ref<any[]>([])
const starChartCanvas = ref<HTMLCanvasElement | null>(null)
const citationChartCanvas = ref<HTMLCanvasElement | null>(null)
const bibtexCopied = ref(false)

let starChart: Chart | null = null
let citationChart: Chart | null = null

async function loadPaper() {
  const paperId = route.params.id
  try {
    const [paperRes, historyRes, citationHistRes, scoresRes, refsRes] = await Promise.all([
      axios.get(`${apiUrl}/api/v1/papers/${paperId}`),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/star-history`).catch(() => ({ data: [] })),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/citation-history`).catch(() => ({ data: [] })),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/hype-scores`).catch(() => ({ data: null })),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/references`).catch(() => ({ data: [] }))
    ])

    paper.value = paperRes.data
    starHistory.value = historyRes.data
    citationHistory.value = citationHistRes.data
    hypeScores.value = scoresRes.data
    references.value = refsRes.data

    // Wait for DOM update then render charts
    await nextTick()
    renderStarChart()
    renderCitationChart()
  } catch (error) {
    console.error('Failed to load paper:', error)
  }
}

function renderStarChart() {
  if (!starChartCanvas.value || starHistory.value.length === 0) return

  // Destroy existing chart
  if (starChart) {
    starChart.destroy()
  }

  const ctx = starChartCanvas.value.getContext('2d')
  if (!ctx) return

  starChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: starHistory.value.map(point => new Date(point.date).toLocaleDateString()),
      datasets: [{
        label: 'GitHub Stars',
        data: starHistory.value.map(point => point.stars),
        borderColor: 'rgb(168, 85, 247)',
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: 'rgb(156, 163, 175)'
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        },
        x: {
          ticks: {
            color: 'rgb(156, 163, 175)',
            maxRotation: 45,
            minRotation: 45
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      }
    }
  })
}

function renderCitationChart() {
  if (!citationChartCanvas.value || citationHistory.value.length === 0) return

  // Destroy existing chart
  if (citationChart) {
    citationChart.destroy()
  }

  const ctx = citationChartCanvas.value.getContext('2d')
  if (!ctx) return

  citationChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: citationHistory.value.map(point => new Date(point.date).toLocaleDateString()),
      datasets: [{
        label: 'Citations',
        data: citationHistory.value.map(point => point.citation_count),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: 'rgb(156, 163, 175)'
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        },
        x: {
          ticks: {
            color: 'rgb(156, 163, 175)',
            maxRotation: 45,
            minRotation: 45
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      }
    }
  })
}

function parseAuthors(authors: string | string[]) {
  if (Array.isArray(authors)) {
    return authors
  }
  // Handle comma-separated string
  return authors.split(',').map(a => a.trim())
}

function formatDate(isoString: string) {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleDateString()
}

function copyBibtex() {
  const authors = parseAuthors(paper.value.authors)
  const year = paper.value.published_date ? new Date(paper.value.published_date).getFullYear() : 'n.d.'
  const firstAuthor = authors[0]?.split(' ').pop() || 'unknown'
  const bibtex = `@article{${firstAuthor}${year},
  title={${paper.value.title}},
  author={${authors.join(' and ')}},
  year={${year}},
  url={${paper.value.pdf_url || paper.value.arxiv_url || ''}}
}`

  navigator.clipboard.writeText(bibtex).then(() => {
    bibtexCopied.value = true
    setTimeout(() => {
      bibtexCopied.value = false
    }, 2000)
  })
}

const goBack = () => {
  router.back()
}

const navigateToHome = () => {
  router.push('/')
}

const navigateToProfile = () => {
  router.push('/profile')
}

const navigateToLogin = () => {
  router.push('/login')
}

const handleSignOut = async () => {
  await authStore.signOut()
  router.push('/')
}

onMounted(() => {
  loadPaper()
})
</script>
