import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import SubjectPage from './pages/SubjectPage'
import DashboardPage from './pages/Dashboard'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main style={{ marginTop: 'var(--navbar-height)' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/subject/:id" element={<SubjectPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}