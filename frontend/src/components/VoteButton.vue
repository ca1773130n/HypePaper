<template>
  <div class="flex items-center gap-2">
    <button
      @click="handleVote('upvote')"
      :class="[
        'p-2 rounded transition-colors',
        userVote === 'upvote'
          ? 'bg-green-100 text-green-600 hover:bg-green-200'
          : 'text-gray-400 hover:text-green-600 hover:bg-gray-100'
      ]"
      :disabled="loading"
      title="Upvote"
    >
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path d="M10 3.586L3.293 10.293a1 1 0 001.414 1.414L10 6.414l5.293 5.293a1 1 0 001.414-1.414L10 3.586z"/>
      </svg>
    </button>

    <span class="min-w-[3ch] text-center font-medium">
      {{ voteCount }}
    </span>

    <button
      @click="handleVote('downvote')"
      :class="[
        'p-2 rounded transition-colors',
        userVote === 'downvote'
          ? 'bg-red-100 text-red-600 hover:bg-red-200'
          : 'text-gray-400 hover:text-red-600 hover:bg-gray-100'
      ]"
      :disabled="loading"
      title="Downvote"
    >
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path d="M10 16.414l6.707-6.707a1 1 0 00-1.414-1.414L10 13.586 4.707 8.293a1 1 0 00-1.414 1.414L10 16.414z"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'

const props = defineProps<{
  paperId: string
  initialVoteCount: number
  initialUserVote?: 'upvote' | 'downvote' | null
}>()

const emit = defineEmits<{
  voteChanged: [voteCount: number, userVote: 'upvote' | 'downvote' | null]
}>()

const authStore = useAuthStore()
const loading = ref(false)
const voteCount = ref(props.initialVoteCount)
const userVote = ref<'upvote' | 'downvote' | null>(props.initialUserVote || null)

const handleVote = async (voteType: 'upvote' | 'downvote') => {
  if (!authStore.isAuthenticated) {
    // Redirect to login
    window.location.href = '/login'
    return
  }

  if (loading.value) return

  loading.value = true
  try {
    // If clicking the same vote, remove it
    if (userVote.value === voteType) {
      await api.delete(`/api/papers/${props.paperId}/vote`)
      voteCount.value += (userVote.value === 'upvote' ? -1 : 1)
      userVote.value = null
    } else {
      // Cast or change vote
      const response = await api.post(`/api/papers/${props.paperId}/vote`, {
        vote_type: voteType
      })

      const previousVote = userVote.value
      userVote.value = voteType

      // Update count based on transition
      if (previousVote === null) {
        voteCount.value += (voteType === 'upvote' ? 1 : -1)
      } else {
        // Changing from one vote to another
        voteCount.value += (voteType === 'upvote' ? 2 : -2)
      }

      // Use server's vote_count if available
      if (response.data.vote_count !== undefined) {
        voteCount.value = response.data.vote_count
      }
    }

    emit('voteChanged', voteCount.value, userVote.value)
  } catch (error: any) {
    console.error('Vote error:', error)
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
  } finally {
    loading.value = false
  }
}
</script>
