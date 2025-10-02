import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import PaperDetailPage from './pages/PaperDetailPage'

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/papers/:paperId" element={<PaperDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
