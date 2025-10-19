<template>
  <div class="metric-graph">
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <div v-else-if="error" class="flex items-center justify-center h-64">
      <p class="text-red-400">{{ error }}</p>
    </div>

    <div v-else-if="chartData" class="h-64">
      <canvas ref="chartCanvas"></canvas>
    </div>

    <div v-else class="flex items-center justify-center h-64">
      <p class="text-gray-500">No data available</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import { api } from '@/services/api'

Chart.register(...registerables)

interface MetricSnapshot {
  snapshot_date: string
  github_stars?: number | null
  citation_count?: number | null
  vote_count?: number | null
  hype_score?: number | null
}

const props = defineProps<{
  paperId: string
  metricType: 'citations' | 'stars' | 'votes' | 'hype_score'
  days?: number
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const chartData = ref<MetricSnapshot[] | null>(null)
let chart: Chart | null = null

const metricConfig = {
  citations: {
    label: 'Citations',
    color: 'rgb(59, 130, 246)',
    field: 'citation_count'
  },
  stars: {
    label: 'GitHub Stars',
    color: 'rgb(168, 85, 247)',
    field: 'github_stars'
  },
  votes: {
    label: 'Net Votes',
    color: 'rgb(34, 197, 94)',
    field: 'vote_count'
  },
  hype_score: {
    label: 'Hype Score',
    color: 'rgb(236, 72, 153)',
    field: 'hype_score'
  }
}

const loadMetrics = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await api.get(`/api/v1/papers/${props.paperId}/metrics`, {
      params: {
        days: props.days || 30
      }
    })
    chartData.value = response.data
    await nextTick()
    renderChart()
  } catch (err: any) {
    console.error('Failed to load metrics:', err)
    // Still render empty chart with axes instead of showing error
    chartData.value = []
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartCanvas.value || chartData.value === null) return

  // Destroy existing chart
  if (chart) {
    chart.destroy()
  }

  const config = metricConfig[props.metricType]
  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  // Prepare data (show empty chart if no data)
  let labels: string[]
  let values: (number | null)[]

  if (chartData.value.length === 0) {
    // Generate placeholder labels for last N days
    const days = props.days || 30
    labels = Array.from({ length: Math.min(days, 7) }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (days - i))
      return date.toLocaleDateString()
    })
    values = Array(labels.length).fill(0)
  } else {
    labels = chartData.value.map(d => new Date(d.snapshot_date).toLocaleDateString())
    values = chartData.value.map(d => {
      const value = d[config.field as keyof MetricSnapshot]
      return value !== null && value !== undefined ? Number(value) : null
    })
  }

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: config.label,
        data: values,
        borderColor: config.color,
        backgroundColor: config.color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        borderWidth: 2,
        borderDash: chartData.value.length === 0 ? [5, 5] : [],
        fill: true,
        tension: 0.4,
        spanGaps: true,
        pointRadius: chartData.value.length === 0 ? 0 : 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: chartData.value.length > 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: config.color,
          borderWidth: 1,
          displayColors: false,
          callbacks: {
            label: (context) => {
              const value = context.parsed.y
              return value !== null ? `${config.label}: ${value.toFixed(2)}` : 'No data'
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: 'rgb(156, 163, 175)'
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
            drawBorder: true
          }
        },
        x: {
          ticks: {
            color: 'rgb(156, 163, 175)',
            maxRotation: 45,
            minRotation: 45
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
            drawBorder: true
          }
        }
      }
    }
  })
}

watch(() => [props.paperId, props.metricType, props.days], () => {
  loadMetrics()
})

onMounted(() => {
  loadMetrics()
})
</script>

<style scoped>
.metric-graph {
  width: 100%;
}
</style>
