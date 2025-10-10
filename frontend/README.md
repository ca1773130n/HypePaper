# HypePaper Frontend

React frontend for discovering and tracking trending research papers.

## Tech Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS (mobile-first)
- **Routing**: React Router v6
- **Charts**: Recharts
- **State Management**: React hooks (useState, useEffect)
- **Data Fetching**: Fetch API with custom hooks

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── ErrorBoundary.tsx     # Error handling
│   │   ├── LoadingStates.tsx     # Skeletons & spinners
│   │   ├── TopicSelector.tsx     # Topic filter chips
│   │   ├── PaperCard.tsx         # Paper list item
│   │   └── MetricChart.tsx       # Time-series visualization
│   ├── pages/            # Route pages
│   │   ├── HomePage.tsx          # Main paper listing
│   │   └── PaperDetailPage.tsx   # Paper details + metrics
│   ├── services/         # API clients
│   │   ├── api.ts        # Base API configuration
│   │   ├── topics.ts     # Topic API calls
│   │   └── papers.ts     # Paper API calls
│   ├── hooks/            # Custom React hooks
│   │   ├── useTopics.ts  # Fetch topics
│   │   ├── usePapers.ts  # Fetch papers with filters
│   │   └── usePaperMetrics.ts # Fetch metric history
│   ├── types/            # TypeScript interfaces
│   │   ├── Paper.ts
│   │   ├── Topic.ts
│   │   └── Metric.ts
│   ├── utils/            # Helper functions
│   │   ├── formatters.ts # Date/number formatting
│   │   └── hypeScore.ts  # Hype score color/label logic
│   ├── App.tsx           # Main app with routing
│   ├── main.tsx          # Entry point
│   └── index.css         # Tailwind directives
├── public/               # Static assets
├── index.html            # HTML template
├── tailwind.config.js    # Tailwind configuration
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite build configuration
└── package.json          # Dependencies
```

## Installation

### Prerequisites

- Node.js 18+ and npm

### Setup

1. **Install dependencies:**
```bash
npm install
```

2. **Configure API endpoint:**

Create `.env.local`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

3. **Start development server:**
```bash
npm run dev
```

App will be available at http://localhost:5173

## Available Scripts

### Development

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality

```bash
# Lint TypeScript/React
npm run lint

# Type checking
npm run type-check
```

## Features

### 1. Topic-Based Filtering

- Browse papers by research topic (neural rendering, diffusion models, 3D reconstruction, etc.)
- Topics loaded from backend `/api/v1/topics`
- Select topic to filter papers

### 2. Paper Listing

- Displays papers with:
  - Title, authors, publication date
  - Hype score with color coding (green/yellow/red)
  - GitHub stars and citation count
  - Trend label (🔥 Hot, 📈 Trending, 📊 Steady, 📉 Cooling)
- Sorting options:
  - **Hype Score**: Highest hype first
  - **Recency**: Newest papers first
  - **Stars**: Most starred first
- Pagination with infinite scroll (future enhancement)

### 3. Paper Details

- Full paper information
- arXiv and GitHub links
- Metric history chart (last 30 days)
- Star growth and citation growth visualization

### 4. Responsive Design

Mobile-first design with breakpoints:
- **Mobile**: 375px+ (single column)
- **Tablet**: 768px+ (2 columns)
- **Desktop**: 1024px+ (3 columns, sidebar)

### 5. Loading States

- **Skeleton screens** during data fetching
- **Shimmer animations** for visual feedback
- **Inline spinners** for updates
- **Full-page overlay** for route transitions

### 6. Error Handling

- **Error boundaries** catch React errors
- **Retry buttons** for failed requests
- **Fallback UI** with helpful messages
- **Development mode** shows detailed error info

## Performance Optimizations

### 1. Code Splitting

```typescript
// Pages loaded lazily with React.lazy()
const HomePage = lazy(() => import('./pages/HomePage'))
const PaperDetailPage = lazy(() => import('./pages/PaperDetailPage'))
```

**Benefits:**
- Reduced initial bundle size
- Faster first page load
- Components loaded on-demand

### 2. API Response Caching

Backend caches hype scores for 1 hour, resulting in:
- First request: ~500ms
- Cached requests: ~50ms (10x faster)

### 3. Optimized Rendering

- Use `React.memo()` for expensive components
- Memoize calculations with `useMemo()`
- Debounce search/filter inputs
- Virtualize long lists (future enhancement)

## Styling Guide

### TailwindCSS Configuration

```javascript
// tailwind.config.js
theme: {
  screens: {
    'sm': '375px',   // Mobile
    'md': '768px',   // Tablet
    'lg': '1024px',  // Desktop
  },
  colors: {
    hype: {
      low: '#6B7280',    // Gray (0-3)
      medium: '#F59E0B', // Orange (4-6)
      high: '#EF4444',   // Red (7-10)
    },
  },
}
```

### Hype Score Color Coding

| Score | Color  | Label       | Meaning               |
|-------|--------|-------------|-----------------------|
| 8-10  | Red    | 🔥 Hot      | Viral/explosive growth|
| 6-8   | Orange | 📈 Trending | Strong growth         |
| 4-6   | Yellow | 📊 Steady   | Moderate activity     |
| 0-4   | Gray   | 📉 Cooling  | Low/declining interest|

### Component Examples

**Paper Card:**
```tsx
<PaperCard
  paper={paper}
  onClick={() => navigate(`/papers/${paper.id}`)}
/>
```

**Loading Skeleton:**
```tsx
{loading ? <PaperListSkeleton count={5} /> : <PaperList papers={papers} />}
```

**Error State:**
```tsx
<ErrorState
  message="Failed to load papers"
  onRetry={() => refetch()}
/>
```

## API Integration

### Base API Configuration

```typescript
// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const fetchApi = async (endpoint: string, options?: RequestInit) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`)
  }

  return response.json()
}
```

### Custom Hooks

**Fetch Papers:**
```typescript
const { papers, loading, error, refetch } = usePapers({
  topicId: selectedTopic,
  sortBy: 'hype_score',
  limit: 20,
})
```

**Fetch Paper Details:**
```typescript
const { paper, metrics, loading } = usePaperDetails(paperId)
```

## Accessibility

- **Semantic HTML**: Proper heading hierarchy, landmarks
- **ARIA labels**: Screen reader support for interactive elements
- **Keyboard navigation**: Tab order, focus management
- **Color contrast**: WCAG AA compliant (4.5:1 ratio)
- **Alt text**: Descriptive text for images/icons

## Testing

### Component Testing (Future)

```bash
# Unit tests with Vitest
npm run test

# Component tests with React Testing Library
npm run test:components

# E2E tests with Playwright
npm run test:e2e
```

### Manual Testing Checklist

1. **Topic Selection**
   - [ ] Topics load on page load
   - [ ] Clicking topic filters papers
   - [ ] "All Topics" shows all papers

2. **Paper Listing**
   - [ ] Papers display with correct data
   - [ ] Sorting works (hype/recency/stars)
   - [ ] Pagination loads more papers
   - [ ] Loading skeletons show during fetch

3. **Paper Details**
   - [ ] Clicking paper navigates to detail page
   - [ ] Metrics chart renders correctly
   - [ ] arXiv/GitHub links work
   - [ ] Back button returns to list

4. **Responsive Design**
   - [ ] Mobile (375px): Single column layout
   - [ ] Tablet (768px): 2 column grid
   - [ ] Desktop (1024px): Sidebar + 2 columns

5. **Error Handling**
   - [ ] Network error shows retry button
   - [ ] Invalid paper ID shows 404 message
   - [ ] Error boundary catches React errors

## Deployment

### Build for Production

```bash
# Create optimized build
npm run build

# Output in dist/ directory
ls dist/
```

### Preview Production Build Locally

```bash
npm run preview
# Visit http://localhost:4173
```

### Deploy to Vercel/Netlify

```bash
# Vercel
vercel deploy

# Netlify
netlify deploy --prod
```

**Environment Variables:**
- Set `VITE_API_BASE_URL` to production API URL
- Example: `https://api.hypepaper.com`

### Static Hosting (Nginx)

```nginx
server {
    listen 80;
    server_name hypepaper.com;
    root /var/www/hypepaper/dist;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Performance Targets

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 2.0s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1

### Lighthouse Scores (Target)

- Performance: 90+
- Accessibility: 95+
- Best Practices: 95+
- SEO: 90+

## Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile Safari (iOS): 14+
- Chrome Android: Last 2 versions

## Contributing

1. Follow React best practices
2. Use TypeScript for type safety
3. Write meaningful component names
4. Keep components under 200 lines
5. Extract reusable logic into hooks
6. Test responsive design at all breakpoints

## Troubleshooting

### API Connection Issues

```bash
# Check API is running
curl http://localhost:8000/api/v1/topics

# Check CORS settings
# Backend should allow frontend origin
```

### Build Failures

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

### Hot Reload Not Working

```bash
# Check file watchers limit (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## License

MIT
