import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface PaperListItem {
  id: string
  title: string
  authors: string[]
  published_date: string
  venue?: string
  github_url?: string
  hype_score: number
  trend_label: string
}

export interface PaperDetail {
  id: string
  arxiv_id?: string
  doi?: string
  title: string
  authors: string[]
  abstract: string
  published_date: string
  venue?: string
  github_url?: string
  arxiv_url?: string
  pdf_url?: string
  hype_score: number
  star_growth_7d: number
  citation_growth_30d: number
  current_stars: number
  trend_label: string
  created_at: string
}

export interface MetricSnapshot {
  snapshot_date: string
  github_stars: number | null
  citation_count: number | null
}

export interface PapersListResponse {
  papers: PaperListItem[]
  total: number
  limit: number
  offset: number
}

export interface PaperMetricsResponse {
  paper_id: string
  metrics: MetricSnapshot[]
}

export const papersService = {
  async getPapers(params?: {
    topic_id?: string
    sort?: 'hype_score' | 'recency' | 'stars'
    limit?: number
    offset?: number
  }): Promise<PapersListResponse> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/papers`, { params })
    return response.data
  },

  async getPaperById(paperId: string): Promise<PaperDetail> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/papers/${paperId}`)
    return response.data
  },

  async getPaperMetrics(paperId: string, days: number = 30): Promise<PaperMetricsResponse> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/papers/${paperId}/metrics`, {
      params: { days },
    })
    return response.data
  },
}
