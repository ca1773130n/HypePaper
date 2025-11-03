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
      // Use backend OAuth redirect proxy for preview deployments
      // This provides a stable redirect URL that works across all Railway preview deployments
      const apiUrl = import.meta.env.VITE_API_URL || window.location.origin
      const backendRedirectProxy = `${apiUrl}/oauth/redirect-proxy`

      // For the proxy to know where to redirect, we need to pass the frontend URL
      // We'll use the state parameter to pass the frontend callback URL
      const frontendCallback = encodeURIComponent(`${window.location.origin}/auth/callback`)

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          // Use backend proxy as stable redirect target
          redirectTo: `${backendRedirectProxy}?frontend_callback=${frontendCallback}`,
          // Skip browser redirect if possible (for debugging)
          skipBrowserRedirect: false
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
      const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession()
      
      // If no session, silently return (user not logged in)
      if (!currentSession || sessionError) {
        user.value = null
        session.value = null
        return
      }

      session.value = currentSession
      user.value = currentSession.user
    } catch (error) {
      // Silently handle - no session is expected when not logged in
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
