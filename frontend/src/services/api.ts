import axios from 'axios'
import { supabase } from '@/lib/supabase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to inject Supabase auth token
api.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
    return config
  },
  (error) => {
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
