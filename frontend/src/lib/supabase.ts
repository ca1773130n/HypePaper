import { createClient } from '@supabase/supabase-js'

// IMPORTANT: Environment variables must be set for authentication to work
// Both VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are required
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Supabase configuration missing!')
  console.error('Required environment variables:')
  console.error('  - VITE_SUPABASE_URL')
  console.error('  - VITE_SUPABASE_ANON_KEY')
  console.error('Current values:')
  console.error('  - VITE_SUPABASE_URL:', supabaseUrl || '(not set)')
  console.error('  - VITE_SUPABASE_ANON_KEY:', supabaseAnonKey ? '(set)' : '(not set)')
  throw new Error('Supabase configuration is required. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables.')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    storageKey: 'hypepaper-auth',
  },
})
