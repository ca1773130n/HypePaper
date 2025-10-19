<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" @click="closeModal">
    <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 transition-opacity bg-gray-900 bg-opacity-75" aria-hidden="true"></div>

      <!-- Modal panel -->
      <div
        class="relative inline-block w-full max-w-2xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-[#1a1f2e] border border-white/10 rounded-2xl shadow-2xl"
        @click.stop
      >
        <!-- Close button -->
        <button
          @click="closeModal"
          class="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <!-- Loading state -->
        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="py-8 text-center">
          <p class="text-red-400">{{ error }}</p>
          <button
            @click="closeModal"
            class="mt-4 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-300 transition-colors"
          >
            Close
          </button>
        </div>

        <!-- Author content -->
        <div v-else-if="author" class="space-y-6">
          <!-- Header -->
          <div class="space-y-2">
            <h2 class="text-3xl font-bold text-white">{{ author.name }}</h2>
            <p v-if="author.primary_affiliation" class="text-lg text-gray-400">
              {{ author.primary_affiliation }}
            </p>
          </div>

          <!-- Statistics -->
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20 rounded-lg">
              <dt class="text-xs text-purple-400 uppercase tracking-wider font-medium mb-1">Papers</dt>
              <dd class="text-2xl font-bold text-white">{{ author.paper_count || 0 }}</dd>
            </div>
            <div class="p-4 bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20 rounded-lg">
              <dt class="text-xs text-blue-400 uppercase tracking-wider font-medium mb-1">Total Citations</dt>
              <dd class="text-2xl font-bold text-white">{{ author.total_citation_count || 0 }}</dd>
            </div>
          </div>

          <!-- Contact info -->
          <div v-if="author.email || author.website_url" class="flex flex-wrap gap-3">
            <a
              v-if="author.email"
              :href="`mailto:${author.email}`"
              class="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-gray-300 hover:text-white transition-all"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span class="text-sm">Email</span>
            </a>
            <a
              v-if="author.website_url"
              :href="author.website_url"
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-gray-300 hover:text-white transition-all"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              <span class="text-sm">Website</span>
            </a>
          </div>

          <!-- Recent papers -->
          <div v-if="recentPapers.length > 0" class="space-y-3">
            <h3 class="text-xl font-semibold text-white">Recent Papers</h3>
            <div class="space-y-2">
              <div
                v-for="paper in recentPapers.slice(0, 5)"
                :key="paper.id"
                class="p-3 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
                @click="navigateToPaper(paper.id)"
              >
                <p class="text-sm text-white font-medium">{{ paper.title }}</p>
                <p class="text-xs text-gray-400 mt-1">{{ formatDate(paper.published_date) }}</p>
              </div>
            </div>
          </div>

          <!-- View all papers button -->
          <button
            @click="viewAllPapers"
            class="w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-lg shadow-lg shadow-purple-500/50 transition-all"
          >
            View All Papers by {{ author.name }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'

interface Author {
  id: number
  name: string
  primary_affiliation?: string
  paper_count?: number
  total_citation_count?: number
  email?: string
  website_url?: string
}

interface Paper {
  id: string
  title: string
  published_date: string
}

const props = defineProps<{
  isOpen: boolean
  authorId: number | null
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const loading = ref(false)
const error = ref<string | null>(null)
const author = ref<Author | null>(null)
const recentPapers = ref<Paper[]>([])

watch(() => props.isOpen, async (isOpen) => {
  if (isOpen && props.authorId) {
    await loadAuthor()
  }
})

const loadAuthor = async () => {
  if (!props.authorId) return

  loading.value = true
  error.value = null

  try {
    const response = await api.get(`/api/authors/${props.authorId}`)
    author.value = response.data

    // Load recent papers
    const papersResponse = await api.get(`/api/papers`, {
      params: {
        author_id: props.authorId,
        limit: 5,
        sort_by: 'published_date'
      }
    })
    recentPapers.value = papersResponse.data.items || []
  } catch (err: any) {
    console.error('Failed to load author:', err)
    error.value = err.response?.data?.detail || 'Failed to load author information'
  } finally {
    loading.value = false
  }
}

const closeModal = () => {
  emit('close')
}

const navigateToPaper = (paperId: string) => {
  closeModal()
  router.push(`/papers/${paperId}`)
}

const viewAllPapers = () => {
  if (author.value) {
    closeModal()
    router.push(`/papers?author_id=${props.authorId}`)
  }
}

const formatDate = (isoString: string) => {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleDateString()
}
</script>
