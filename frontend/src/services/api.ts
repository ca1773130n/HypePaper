import axios from 'axios'
import { supabase } from '@/lib/supabase'

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to inject Supabase auth token
api.interceptors.request.use(
  async (config) => {
    try {
      console.log('[API] Making request to:', config.url)
      const { data: { session }, error } = await supabase.auth.getSession()

      if (error) {
        console.error('[API] Error getting session:', error)
        return config
      }

      if (session?.access_token) {
        console.log('[API] Adding auth token to request')
        // Ensure headers object exists
        if (!config.headers) {
          config.headers = {} as any
        }
        config.headers.Authorization = `Bearer ${session.access_token}`
      } else {
        console.warn('[API] No session or access token available')
      }
    } catch (error) {
      console.error('[API] Exception in request interceptor:', error)
    }
    return config
  },
  (error) => {
    console.error('[API] Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for better error logging
api.interceptors.response.use(
  (response) => {
    console.log('[API] Response received:', response.config.url, response.status)
    return response
  },
  (error) => {
    if (error.response) {
      console.error('[API] Response error:', {
        url: error.config?.url,
        status: error.response.status,
        data: error.response.data,
        headers: error.response.headers
      })
    } else {
      console.error('[API] Network error:', error.message)
    }
    return Promise.reject(error)
  }
)

export interface Topic {
  id: string
  name: string
  description: string
  keywords?: string[]
  is_system: boolean
  user_id?: string | null
  created_at: string
  paper_count?: number
}

export interface Paper {
  id: string
  title: string
  authors: string[]
  abstract: string
  published_date: string
  venue: string | null
  github_url: string | null
  github_stars: number | null
  hype_score: number
  trend_label: string
}

export interface HypeScore {
  paper_id: string
  score_date: string
  total_score: number
  star_velocity_score: number
  citation_velocity_score: number
  absolute_metrics_score: number
  recency_score: number
}

export interface MetricSnapshot {
  paper_id: string
  snapshot_date: string
  github_stars: number | null
  citation_count: number | null
}

export interface PapersListResponse {
  papers: Paper[]
  total: number
  limit: number
  offset: number
}

export interface TopicsListResponse {
  topics: Topic[]
  total: number
}

export const topicsApi = {
  getAll: () => api.get<TopicsListResponse>('/api/v1/topics'),
  getById: (id: string) => api.get<Topic>(`/api/v1/topics/${id}`),
}

export const papersApi = {
  getAll: (params?: {
    topic_id?: string
    sort_by?: 'hype_score' | 'published_date' | 'stars' | 'citations'
    limit?: number
    offset?: number
  }) => api.get<PapersListResponse>('/api/v1/papers', { params }),
  getById: (id: string) => api.get<Paper>(`/api/v1/papers/${id}`),
  getMetrics: (id: string, params?: { days?: number }) =>
    api.get<MetricSnapshot[]>(`/api/v1/papers/${id}/metrics`, { params }),
  getHypeScore: (id: string) => api.get<HypeScore>(`/api/v1/papers/${id}/hype-score`),
}
