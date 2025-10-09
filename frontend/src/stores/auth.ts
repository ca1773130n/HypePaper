import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase } from '@/lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const session = ref<Session | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!session.value)

  async function signInWithGoogle() {
    loading.value = true
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      if (error) throw error
      return data
    } finally {
      loading.value = false
    }
  }

  async function signOut() {
    loading.value = true
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      user.value = null
      session.value = null
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    loading.value = true
    try {
      const { data: { user: currentUser }, error } = await supabase.auth.getUser()
      if (error) throw error
      user.value = currentUser

      const { data: { session: currentSession } } = await supabase.auth.getSession()
      session.value = currentSession
    } catch (error) {
      console.error('Error fetching user:', error)
      user.value = null
      session.value = null
    } finally {
      loading.value = false
    }
  }

  // Listen for auth state changes
  supabase.auth.onAuthStateChange((_event, newSession) => {
    session.value = newSession
    user.value = newSession?.user ?? null
  })

  return {
    user,
    session,
    loading,
    isAuthenticated,
    signInWithGoogle,
    signOut,
    fetchUser
  }
})
