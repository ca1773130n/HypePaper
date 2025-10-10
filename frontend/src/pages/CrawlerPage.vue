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
            <h1 class="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent cursor-pointer" @click="navigateToHome">
              HypePaper
            </h1>
            <p class="mt-2 text-gray-400 text-sm font-light tracking-wide">Crawl and discover research papers</p>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="navigateToHome"
              class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-purple-500/50 transition-all text-gray-200 text-sm font-medium"
            >
              ← Home
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
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid grid-cols-12 gap-8">
        <!-- Sidebar -->
        <aside class="col-span-3">
          <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 space-y-2 sticky top-8">
            <button
              @click="currentView = 'active-crawlers'"
              :class="[
                'w-full text-left px-4 py-3 rounded-xl transition-all',
                currentView === 'active-crawlers'
                  ? 'bg-purple-500/20 border border-purple-500/50 text-purple-300'
                  : 'bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10'
              ]"
            >
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <span class="font-medium">Active Crawlers</span>
              </div>
            </button>

            <button
              @click="currentView = 'new-crawler'"
              :class="[
                'w-full text-left px-4 py-3 rounded-xl transition-all',
                currentView === 'new-crawler'
                  ? 'bg-purple-500/20 border border-purple-500/50 text-purple-300'
                  : 'bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10'
              ]"
            >
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span class="font-medium">Add New Crawler</span>
              </div>
            </button>

            <button
              disabled
              class="w-full text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-gray-500 cursor-not-allowed opacity-50"
            >
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span class="font-medium">Custom Workflow</span>
              </div>
              <p class="text-xs text-gray-600 mt-1 ml-8">Coming soon</p>
            </button>
          </div>
        </aside>

        <!-- Main Content Area -->
        <div class="col-span-9">
          <!-- Active Crawlers View (Default) -->
          <div v-if="currentView === 'active-crawlers'">
            <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-8">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-white">Active Crawler Jobs</h2>
                <button
                  @click="loadCrawlerJobs"
                  class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-gray-300 text-sm"
                >
                  <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>

              <!-- Jobs Table -->
              <div v-if="crawlerJobs.length === 0" class="text-center py-12 text-gray-500">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p>No active crawler jobs</p>
                <p class="text-sm mt-2">Background jobs with reference crawling will appear here</p>
              </div>

              <div v-else class="space-y-4">
                <div
                  v-for="job in crawlerJobs"
                  :key="job.job_id"
                  @click="selectedJob = job"
                  class="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-purple-500/50 cursor-pointer transition-all"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-3">
                        <span class="font-mono text-sm text-purple-300">{{ job.job_id }}</span>
                        <span
                          :class="[
                            'px-2 py-1 rounded text-xs font-medium',
                            job.status === 'processing' ? 'bg-blue-500/20 text-blue-300' :
                            job.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                            'bg-red-500/20 text-red-300'
                          ]"
                        >
                          {{ job.status }}
                        </span>
                      </div>
                      <div class="mt-2 space-y-2">
                        <div class="flex items-center gap-2 text-sm">
                          <span class="text-gray-500">Type:</span>
                          <span class="text-gray-300 capitalize">{{ job.source_type || 'arxiv' }}</span>
                          <span class="text-gray-500 ml-4">Keywords:</span>
                          <span class="text-gray-300">{{ job.keywords || 'N/A' }}</span>
                          <span v-if="job.period" class="text-gray-500 ml-4">Period:</span>
                          <span v-if="job.period" class="text-purple-400 capitalize">{{ job.period }}</span>
                        </div>
                        <div class="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <p class="text-gray-500 text-xs">Started</p>
                            <p class="text-gray-300">{{ formatDate(job.started_at) }}</p>
                          </div>
                          <div>
                            <p class="text-gray-500 text-xs">Uptime</p>
                            <p class="text-gray-300">{{ calculateUptime(job.started_at, job.status) }}</p>
                          </div>
                          <div>
                            <p class="text-gray-500 text-xs">Papers Crawled</p>
                            <p class="text-gray-300">{{ job.papers_crawled || 0 }}</p>
                          </div>
                          <div>
                            <p class="text-gray-500 text-xs">Depth</p>
                            <p class="text-gray-300">{{ job.reference_depth || 'N/A' }}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Job Logs -->
              <div v-if="selectedJob" class="mt-6 p-6 rounded-xl bg-black/20 border border-white/10">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-lg font-bold text-white">Real-time Logs</h3>
                  <button
                    @click="selectedJob = null"
                    class="text-gray-400 hover:text-white"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div class="bg-black/40 rounded-lg p-4 font-mono text-xs text-gray-300 max-h-96 overflow-y-auto">
                  <div v-if="jobLogs.length === 0" class="text-gray-500">Loading logs...</div>
                  <div v-for="(log, idx) in jobLogs" :key="idx" class="mb-1">
                    <span class="text-gray-500">{{ log.timestamp }}</span>
                    <span :class="log.level === 'ERROR' ? 'text-red-400' : 'text-gray-300'"> {{ log.message }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Add New Crawler View -->
          <div v-if="currentView === 'new-crawler'">
            <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-8">
              <h2 class="text-2xl font-bold text-white mb-6">Add New Crawler</h2>

        <!-- Crawl Form -->
        <div class="space-y-6">
          <!-- Source Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">Source</label>
            <select
              v-model="crawlSource"
              class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            >
              <option value="arxiv">arXiv</option>
              <option value="conference">Conference</option>
              <option value="citations">Citation Network</option>
            </select>
          </div>

          <!-- ArXiv Fields -->
          <template v-if="crawlSource === 'arxiv'">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Keywords
                <span class="text-gray-500 text-xs ml-2">(space-separated)</span>
              </label>
              <input
                v-model="arxivKeywords"
                type="text"
                placeholder="e.g., neural networks transformer"
                class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Category (optional)
                <span class="text-gray-500 text-xs ml-2">(e.g., cs.AI, cs.CV)</span>
              </label>
              <input
                v-model="arxivCategory"
                type="text"
                placeholder="e.g., cs.LG"
                class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Maximum Results (1-1000)</label>
              <input
                v-model.number="arxivMaxResults"
                type="number"
                min="1"
                max="1000"
                class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>

            <!-- Reference Crawling -->
            <div class="border-t border-white/10 pt-4">
              <label class="flex items-center gap-3 cursor-pointer">
                <input
                  v-model="crawlReferences"
                  type="checkbox"
                  class="w-4 h-4 rounded bg-white/5 border-white/10 text-purple-500 focus:ring-2 focus:ring-purple-500/50"
                />
                <div>
                  <span class="text-sm font-medium text-gray-300">Crawl References (Citation Network)</span>
                  <p class="text-xs text-gray-500 mt-1">Extract and crawl papers from reference lists recursively</p>
                </div>
              </label>

              <div v-if="crawlReferences" class="mt-4 ml-7 space-y-3">
                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    Reference Crawl Depth (1-3)
                  </label>
                  <input
                    v-model.number="referenceDepth"
                    type="number"
                    min="1"
                    max="3"
                    class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  />
                  <p class="text-xs text-gray-500 mt-2">
                    Depth 1: Crawl references of initial papers<br/>
                    Depth 2: Crawl references of references (exponential growth)<br/>
                    Depth 3: Maximum depth (may take significant time)
                  </p>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-300 mb-2">
                    Crawling Period (optional)
                  </label>
                  <select
                    v-model="crawlPeriod"
                    class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  >
                    <option value="">One-time (default)</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                  <p class="text-xs text-gray-500 mt-2">
                    Periodic crawling will update metrics (GitHub stars, citations) for existing papers on a schedule
                  </p>
                </div>
              </div>
            </div>
          </template>

          <!-- Conference Fields -->
          <template v-if="crawlSource === 'conference'">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Conference Name</label>
              <input
                v-model="conferenceName"
                type="text"
                placeholder="e.g., NeurIPS, CVPR, ICLR"
                class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Year</label>
              <input
                v-model.number="conferenceYear"
                type="number"
                min="2000"
                :max="new Date().getFullYear()"
                placeholder="e.g., 2024"
                class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
          </template>

          <!-- Citations Fields -->
          <template v-if="crawlSource === 'citations'">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Seed Paper IDs</label>
              <textarea
                v-model="seedPaperIds"
                rows="3"
                placeholder="Enter paper IDs (one per line)"
                class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Citation Depth (1-3)</label>
              <input
                v-model.number="citationDepth"
                type="number"
                min="1"
                max="3"
                class="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
          </template>

          <!-- Crawl Button -->
          <button
            @click="startCrawl"
            :disabled="crawling || !isFormValid"
            class="w-full px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium shadow-lg shadow-purple-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ crawling ? 'Crawling...' : 'Start Crawling' }}
          </button>
        </div>

        <!-- Status Messages -->
        <div v-if="statusMessage" class="mt-6 p-4 rounded-xl" :class="statusType === 'error' ? 'bg-red-500/10 border border-red-500/20' : 'bg-green-500/10 border border-green-500/20'">
          <p :class="statusType === 'error' ? 'text-red-300' : 'text-green-300'">{{ statusMessage }}</p>
        </div>

        <!-- Job ID -->
        <div v-if="jobId" class="mt-4 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
          <p class="text-sm text-blue-300">Job ID: <span class="font-mono">{{ jobId }}</span></p>
          <p class="text-xs text-gray-400 mt-1">Job submitted successfully. Papers will be crawled in the background.</p>
        </div>
          </div>
        </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// View state
const currentView = ref('active-crawlers')

const crawlSource = ref('arxiv')
const crawling = ref(false)
const statusMessage = ref('')
const statusType = ref<'success' | 'error'>('success')
const jobId = ref('')

// ArXiv fields
const arxivKeywords = ref('')
const arxivCategory = ref('')
const arxivMaxResults = ref(100)
const crawlReferences = ref(false)
const referenceDepth = ref(1)
const crawlPeriod = ref('')

// Conference fields
const conferenceName = ref('')
const conferenceYear = ref(new Date().getFullYear())

// Citations fields
const seedPaperIds = ref('')
const citationDepth = ref(1)

// Manage crawlers
const crawlerJobs = ref<any[]>([])
const selectedJob = ref<any>(null)
const jobLogs = ref<any[]>([])
let logsInterval: any = null

const isFormValid = computed(() => {
  if (crawlSource.value === 'arxiv') {
    return arxivKeywords.value || arxivCategory.value
  } else if (crawlSource.value === 'conference') {
    return conferenceName.value && conferenceYear.value
  } else if (crawlSource.value === 'citations') {
    return seedPaperIds.value.trim().length > 0
  }
  return false
})

const startCrawl = async () => {
  crawling.value = true
  statusMessage.value = ''
  jobId.value = ''

  try {
    const payload: any = {
      source: crawlSource.value,
      priority: 'normal',
      enable_enrichment: false
    }

    if (crawlSource.value === 'arxiv') {
      if (arxivKeywords.value) payload.arxiv_keywords = arxivKeywords.value
      if (arxivCategory.value) payload.arxiv_category = arxivCategory.value
      payload.arxiv_max_results = arxivMaxResults.value
      payload.crawl_references = crawlReferences.value
      if (crawlReferences.value) {
        payload.reference_depth = referenceDepth.value
        if (crawlPeriod.value) {
          payload.period = crawlPeriod.value
        }
      }
    } else if (crawlSource.value === 'conference') {
      payload.conference_name = conferenceName.value
      payload.conference_year = conferenceYear.value
    } else if (crawlSource.value === 'citations') {
      payload.seed_paper_ids = seedPaperIds.value.split('\n').map(id => id.trim()).filter(Boolean)
      payload.citation_depth = citationDepth.value
    }

    const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/jobs/crawl-sync`, payload)

    const data = response.data
    let message = ''

    // Check if it's an async background job (reference crawling)
    if (data.status === 'processing') {
      message = data.message || 'Reference crawling started in background. Check backend logs for progress.'
    } else {
      // Synchronous crawl response
      message = `Successfully crawled ${data.papers_crawled} papers, stored ${data.papers_stored} new papers`

      if (data.references_crawled > 0) {
        message += `, and ${data.references_crawled} referenced papers`
      }
    }

    jobId.value = data.job_id || 'N/A'
    statusMessage.value = message
    statusType.value = 'success'
  } catch (error: any) {
    statusMessage.value = error.response?.data?.detail || 'Failed to start crawl job. Please try again.'
    statusType.value = 'error'
  } finally {
    crawling.value = false
  }
}

const navigateToHome = () => {
  router.push('/')
}

const navigateToProfile = () => {
  router.push('/profile')
}

const handleSignOut = async () => {
  await authStore.signOut()
  router.push('/')
}

// Manage crawlers functions
const loadCrawlerJobs = async () => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/jobs/crawler-jobs`)
    crawlerJobs.value = response.data.jobs || []
  } catch (error) {
    console.error('Failed to load crawler jobs:', error)
  }
}

const loadJobLogs = async (jobId: string) => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/jobs/crawler-logs/${jobId}`)
    jobLogs.value = response.data.logs || []
  } catch (error) {
    console.error('Failed to load job logs:', error)
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  // Backend sends UTC time, convert to local timezone
  const date = new Date(dateStr + 'Z') // Add 'Z' to indicate UTC
  return date.toLocaleString()
}

const calculateUptime = (startedAt: string, status: string) => {
  if (!startedAt) return 'N/A'

  const start = new Date(startedAt + 'Z').getTime() // Add 'Z' to indicate UTC
  const now = Date.now()
  const diff = now - start

  // If completed, don't show increasing uptime
  if (status === 'completed' || status === 'failed') {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    if (hours > 0) return `${hours}h ${minutes}m`
    if (minutes > 0) return `${minutes}m`
    return '<1m'
  }

  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  if (hours > 0) return `${hours}h ${minutes}m`
  if (minutes > 0) return `${minutes}m ${seconds}s`
  return `${seconds}s`
}

// Watch for selected job changes
watch(selectedJob, (newJob) => {
  if (logsInterval) {
    clearInterval(logsInterval)
    logsInterval = null
  }

  if (newJob) {
    jobLogs.value = []
    loadJobLogs(newJob.job_id)

    // Poll logs every 2 seconds
    logsInterval = setInterval(() => {
      loadJobLogs(newJob.job_id)
    }, 2000)
  }
})

// Load jobs when switching to active crawlers view
watch(currentView, (newView) => {
  if (newView === 'active-crawlers') {
    loadCrawlerJobs()
  }
})

onMounted(() => {
  if (currentView.value === 'active-crawlers') {
    loadCrawlerJobs()
  }
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

.delay-1000 {
  animation-delay: 1000ms;
}
</style>
