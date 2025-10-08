<template>
  <div class="min-h-screen bg-[#0A0F1E]">
    <!-- Animated Background -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-0 right-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute bottom-0 left-1/3 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-700"></div>
    </div>

    <!-- Header -->
    <header class="relative border-b border-white/10 backdrop-blur-xl bg-white/5">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <button
          @click="router.back()"
          class="group inline-flex items-center gap-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
        >
          <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Papers
        </button>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col justify-center items-center py-24">
      <div class="relative">
        <div class="w-16 h-16 border-4 border-purple-500/20 rounded-full"></div>
        <div class="w-16 h-16 border-4 border-purple-500 rounded-full animate-spin border-t-transparent absolute top-0"></div>
      </div>
      <p class="mt-4 text-gray-400 text-sm">Loading paper details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-red-500/10 backdrop-blur-xl border border-red-500/20 rounded-2xl p-6 text-red-300">
        <div class="flex items-start gap-3">
          <svg class="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Paper Details -->
    <main v-else-if="paper" class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid gap-8 lg:grid-cols-3">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-8">
          <!-- Paper Info -->
          <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8">
            <!-- Categories -->
            <div class="flex flex-wrap gap-2 mb-6">
              <span
                v-for="category in paper.categories"
                :key="category"
                class="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-300 border border-blue-500/30"
              >
                {{ category }}
              </span>
            </div>

            <!-- Title -->
            <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-300 via-purple-300 to-pink-300 bg-clip-text text-transparent mb-6 leading-tight">
              {{ paper.title }}
            </h1>

            <!-- Metadata -->
            <div class="grid gap-4 mb-8 p-6 bg-white/5 rounded-xl border border-white/5">
              <div class="flex items-start gap-3">
                <svg class="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <div>
                  <p class="text-xs text-gray-500 mb-1">Authors</p>
                  <p class="text-sm text-gray-300">{{ paper.authors.join(', ') }}</p>
                </div>
              </div>

              <div class="flex items-start gap-3">
                <svg class="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <div>
                  <p class="text-xs text-gray-500 mb-1">Published</p>
                  <p class="text-sm text-gray-300">{{ formatDate(paper.published_date) }}</p>
                </div>
              </div>

              <div v-if="paper.arxiv_id" class="flex items-start gap-3">
                <svg class="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div>
                  <p class="text-xs text-gray-500 mb-1">arXiv ID</p>
                  <a
                    :href="`https://arxiv.org/abs/${paper.arxiv_id}`"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-sm text-blue-400 hover:text-blue-300 hover:underline inline-flex items-center gap-1 transition-colors"
                  >
                    {{ paper.arxiv_id }}
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              </div>

              <div v-if="paper.github_url" class="flex items-start gap-3">
                <svg class="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                <div>
                  <p class="text-xs text-gray-500 mb-1">GitHub Repository</p>
                  <a
                    :href="paper.github_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-sm text-purple-400 hover:text-purple-300 hover:underline inline-flex items-center gap-1 transition-colors break-all"
                  >
                    {{ paper.github_url }}
                    <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>

            <!-- Abstract -->
            <div>
              <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span class="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></span>
                Abstract
              </h2>
              <p class="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {{ paper.abstract }}
              </p>
            </div>
          </div>

          <!-- Metrics Chart -->
          <div v-if="metrics.length > 0" class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8">
            <TabsRoot v-model="activeMetricTab" class="w-full">
              <TabsList class="flex gap-2 mb-6 bg-white/5 p-1 rounded-xl">
                <TabsTrigger
                  value="stars"
                  class="flex-1 px-4 py-3 text-sm font-medium text-gray-400 rounded-lg transition-all data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500 data-[state=active]:text-white data-[state=active]:shadow-lg"
                >
                  ⭐ GitHub Stars
                </TabsTrigger>
                <TabsTrigger
                  value="citations"
                  class="flex-1 px-4 py-3 text-sm font-medium text-gray-400 rounded-lg transition-all data-[state=active]:bg-gradient-to-r data-[state=active]:from-green-500 data-[state=active]:to-emerald-500 data-[state=active]:text-white data-[state=active]:shadow-lg"
                >
                  📚 Citations
                </TabsTrigger>
              </TabsList>

              <TabsContent value="stars" class="pt-4">
                <div class="h-80 bg-white/5 rounded-xl p-6 border border-white/5">
                  <svg class="w-full h-full" viewBox="0 0 600 280" preserveAspectRatio="none">
                    <!-- Grid lines -->
                    <line v-for="i in 5" :key="'h-' + i" x1="20" :y1="20 + (i * 52)" x2="580" :y2="20 + (i * 52)" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1" />
                    <line v-for="i in 10" :key="'v-' + i" :x1="20 + (i * 56)" y1="20" :x2="20 + (i * 56)" y2="260" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1" />

                    <!-- Gradient fill under line -->
                    <defs>
                      <linearGradient id="starsGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#3B82F6;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#3B82F6;stop-opacity:0" />
                      </linearGradient>
                    </defs>
                    <polygon :points="`20,260 ${getChartPoints(metrics.map(m => m.github_stars || 0))} 580,260`" fill="url(#starsGradient)" />

                    <!-- Line -->
                    <polyline
                      :points="getChartPoints(metrics.map(m => m.github_stars || 0))"
                      fill="none"
                      stroke="#3B82F6"
                      stroke-width="3"
                    />

                    <!-- Points -->
                    <g v-for="(point, i) in getChartPoints(metrics.map(m => m.github_stars || 0)).split(' ')" :key="i">
                      <circle :cx="point.split(',')[0]" :cy="point.split(',')[1]" r="5" fill="#3B82F6" class="cursor-pointer hover:r-7 transition-all" />
                      <circle :cx="point.split(',')[0]" :cy="point.split(',')[1]" r="3" fill="#fff" />
                    </g>
                  </svg>
                </div>
              </TabsContent>

              <TabsContent value="citations" class="pt-4">
                <div class="h-80 bg-white/5 rounded-xl p-6 border border-white/5">
                  <svg class="w-full h-full" viewBox="0 0 600 280" preserveAspectRatio="none">
                    <!-- Grid lines -->
                    <line v-for="i in 5" :key="'h-' + i" x1="20" :y1="20 + (i * 52)" x2="580" :y2="20 + (i * 52)" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1" />
                    <line v-for="i in 10" :key="'v-' + i" :x1="20 + (i * 56)" y1="20" :x2="20 + (i * 56)" y2="260" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1" />

                    <!-- Gradient fill -->
                    <defs>
                      <linearGradient id="citationsGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#10B981;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#10B981;stop-opacity:0" />
                      </linearGradient>
                    </defs>
                    <polygon :points="`20,260 ${getChartPoints(metrics.map(m => m.citation_count || 0))} 580,260`" fill="url(#citationsGradient)" />

                    <!-- Line -->
                    <polyline
                      :points="getChartPoints(metrics.map(m => m.citation_count || 0))"
                      fill="none"
                      stroke="#10B981"
                      stroke-width="3"
                    />

                    <!-- Points -->
                    <g v-for="(point, i) in getChartPoints(metrics.map(m => m.citation_count || 0)).split(' ')" :key="i">
                      <circle :cx="point.split(',')[0]" :cy="point.split(',')[1]" r="5" fill="#10B981" class="cursor-pointer hover:r-7 transition-all" />
                      <circle :cx="point.split(',')[0]" :cy="point.split(',')[1]" r="3" fill="#fff" />
                    </g>
                  </svg>
                </div>
              </TabsContent>
            </TabsRoot>
          </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <!-- Hype Score Card -->
          <div v-if="hypeScore" class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 sticky top-6">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <span class="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></span>
              Hype Score
            </h2>

            <!-- Main Score -->
            <div class="relative mb-8">
              <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl"></div>
              <div class="relative text-center bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl p-6 border border-purple-500/20">
                <div class="text-6xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  {{ hypeScore.total_score.toFixed(1) }}
                </div>
                <p class="text-sm text-gray-400 mt-2">Overall Score</p>
              </div>
            </div>

            <!-- Score Breakdown -->
            <div class="space-y-4">
              <div>
                <div class="flex justify-between text-sm mb-2">
                  <span class="text-gray-300 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                    Star Velocity
                  </span>
                  <span class="font-bold text-blue-300">{{ hypeScore.star_velocity_score.toFixed(1) }}</span>
                </div>
                <div class="w-full bg-white/5 rounded-full h-2.5 overflow-hidden">
                  <div
                    class="bg-gradient-to-r from-blue-500 to-blue-400 h-2.5 rounded-full transition-all duration-500 shadow-lg shadow-blue-500/50"
                    :style="{ width: `${(hypeScore.star_velocity_score / 100) * 100}%` }"
                  ></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-sm mb-2">
                  <span class="text-gray-300 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-green-500"></span>
                    Citation Velocity
                  </span>
                  <span class="font-bold text-green-300">{{ hypeScore.citation_velocity_score.toFixed(1) }}</span>
                </div>
                <div class="w-full bg-white/5 rounded-full h-2.5 overflow-hidden">
                  <div
                    class="bg-gradient-to-r from-green-500 to-emerald-400 h-2.5 rounded-full transition-all duration-500 shadow-lg shadow-green-500/50"
                    :style="{ width: `${(hypeScore.citation_velocity_score / 100) * 100}%` }"
                  ></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-sm mb-2">
                  <span class="text-gray-300 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-purple-500"></span>
                    Absolute Metrics
                  </span>
                  <span class="font-bold text-purple-300">{{ hypeScore.absolute_metrics_score.toFixed(1) }}</span>
                </div>
                <div class="w-full bg-white/5 rounded-full h-2.5 overflow-hidden">
                  <div
                    class="bg-gradient-to-r from-purple-500 to-purple-400 h-2.5 rounded-full transition-all duration-500 shadow-lg shadow-purple-500/50"
                    :style="{ width: `${(hypeScore.absolute_metrics_score / 100) * 100}%` }"
                  ></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-sm mb-2">
                  <span class="text-gray-300 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-orange-500"></span>
                    Recency
                  </span>
                  <span class="font-bold text-orange-300">{{ hypeScore.recency_score.toFixed(1) }}</span>
                </div>
                <div class="w-full bg-white/5 rounded-full h-2.5 overflow-hidden">
                  <div
                    class="bg-gradient-to-r from-orange-500 to-orange-400 h-2.5 rounded-full transition-all duration-500 shadow-lg shadow-orange-500/50"
                    :style="{ width: `${(hypeScore.recency_score / 100) * 100}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Current Metrics -->
          <div v-if="latestMetric" class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
            <h2 class="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <span class="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></span>
              Current Metrics
            </h2>
            <dl class="space-y-5">
              <div class="bg-white/5 rounded-xl p-4 border border-white/5">
                <dt class="text-xs text-gray-500 mb-1">GitHub Stars</dt>
                <dd class="text-3xl font-bold bg-gradient-to-r from-blue-300 to-blue-400 bg-clip-text text-transparent">
                  {{ latestMetric.github_stars?.toLocaleString() || 'N/A' }}
                </dd>
              </div>
              <div class="bg-white/5 rounded-xl p-4 border border-white/5">
                <dt class="text-xs text-gray-500 mb-1">Citations</dt>
                <dd class="text-3xl font-bold bg-gradient-to-r from-green-300 to-emerald-400 bg-clip-text text-transparent">
                  {{ latestMetric.citation_count?.toLocaleString() || 'N/A' }}
                </dd>
              </div>
              <div class="bg-white/5 rounded-xl p-4 border border-white/5">
                <dt class="text-xs text-gray-500 mb-1">Last Updated</dt>
                <dd class="text-sm text-gray-300">
                  {{ formatDate(latestMetric.snapshot_date) }}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  TabsRoot,
  TabsList,
  TabsTrigger,
  TabsContent,
} from 'reka-ui'
import { papersApi, type Paper, type HypeScore, type MetricSnapshot } from '@/services/api'

const route = useRoute()
const router = useRouter()

const paper = ref<Paper | null>(null)
const hypeScore = ref<HypeScore | null>(null)
const metrics = ref<MetricSnapshot[]>([])
const activeMetricTab = ref('stars')
const loading = ref(false)
const error = ref('')

const latestMetric = computed(() => metrics.value[metrics.value.length - 1])

const fetchPaperDetails = async () => {
  const paperId = route.params.id as string
  loading.value = true
  error.value = ''

  try {
    const [paperRes, metricsRes, hypeRes] = await Promise.allSettled([
      papersApi.getById(paperId),
      papersApi.getMetrics(paperId, { days: 30 }),
      papersApi.getHypeScore(paperId),
    ])

    if (paperRes.status === 'fulfilled') {
      paper.value = paperRes.value.data
    } else {
      throw new Error('Failed to load paper')
    }

    if (metricsRes.status === 'fulfilled') {
      metrics.value = metricsRes.value.data
    }

    if (hypeRes.status === 'fulfilled') {
      hypeScore.value = hypeRes.value.data
    }
  } catch (err) {
    error.value = 'Failed to load paper details. Please try again.'
    console.error('Failed to fetch paper details:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const getChartPoints = (data: number[]): string => {
  if (data.length === 0) return ''

  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1

  const width = 600
  const height = 280
  const padding = 20

  return data
    .map((value, index) => {
      const x = padding + (index / (data.length - 1 || 1)) * (width - 2 * padding)
      const y = height - padding - ((value - min) / range) * (height - 2 * padding)
      return `${x},${y}`
    })
    .join(' ')
}

onMounted(() => {
  fetchPaperDetails()
})
</script>

<style scoped>
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
</style>
