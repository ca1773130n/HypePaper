import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface Topic {
  id: string
  name: string
  description?: string
  keywords?: string[]
  paper_count: number
  created_at: string
}

export interface TopicsListResponse {
  topics: Topic[]
  total: number
}

export interface TopicDetail {
  id: string
  name: string
  description?: string
  keywords?: string[]
  created_at: string
}

export const topicsService = {
  async getTopics(): Promise<TopicsListResponse> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/topics`)
    return response.data
  },

  async getTopicById(topicId: string): Promise<TopicDetail> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/topics/${topicId}`)
    return response.data
  },
}
