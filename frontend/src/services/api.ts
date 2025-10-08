import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Topic {
  id: string
  name: string
  description: string
  created_at: string
}

export interface Paper {
  id: string
  title: string
  authors: string[]
  arxiv_id: string
  published_date: string
  abstract: string
  github_url: string | null
  primary_category: string
  categories: string[]
  created_at: string
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

export const topicsApi = {
  getAll: () => api.get<Topic[]>('/api/v1/topics'),
  getById: (id: string) => api.get<Topic>(`/api/v1/topics/${id}`),
}

export const papersApi = {
  getAll: (params?: {
    topic_id?: string
    sort_by?: 'hype_score' | 'published_date' | 'stars' | 'citations'
    limit?: number
    offset?: number
  }) => api.get<Paper[]>('/api/v1/papers', { params }),
  getById: (id: string) => api.get<Paper>(`/api/v1/papers/${id}`),
  getMetrics: (id: string, params?: { days?: number }) =>
    api.get<MetricSnapshot[]>(`/api/v1/papers/${id}/metrics`, { params }),
  getHypeScore: (id: string) => api.get<HypeScore>(`/api/v1/papers/${id}/hype-score`),
}
