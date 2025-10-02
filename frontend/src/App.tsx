import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LoadingOverlay } from './components/LoadingStates'

// Lazy load page components for code splitting
const HomePage = lazy(() => import('./pages/HomePage'))
const PaperDetailPage = lazy(() => import('./pages/PaperDetailPage'))

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<LoadingOverlay message="Loading HypePaper..." />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/papers/:paperId" element={<PaperDetailPage />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
