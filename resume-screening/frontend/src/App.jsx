import { useState, useEffect, useCallback } from 'react'
import Navbar from './components/Navbar'
import ResumeUpload from './components/ResumeUpload'
import ResumeList from './components/ResumeList'
import ResumeDetailModal from './components/ResumeDetailModal'
import JobDescriptions from './components/JobDescriptions'
import PipelineOverview from './components/PipelineOverview'
import Dashboard from './components/Dashboard'
import Footer from './components/Footer'

export default function App() {
  const [activeTab, setActiveTab] = useState('resumes') // 'resumes', 'jds', 'dashboard', 'pipeline'
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedResume, setSelectedResume] = useState(null)
  const [toasts, setToasts] = useState([])

  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random()
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4500)
  }, [])

  const fetchResumes = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/resumes/?limit=100')
      if (res.ok) {
        const data = await res.json()
        setResumes(data.resumes || [])
      }
    } catch {
      // Backend may be booting or offline
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchResumes()
  }, [fetchResumes])

  const handleUploadSuccess = (newResume) => {
    setResumes((prev) => [newResume, ...prev.filter((r) => r.id !== newResume.id)])
    setSelectedResume(newResume)
  }

  const handleDeleteResume = async (id, filename) => {
    if (!window.confirm(`Delete resume "${filename}"? This cannot be undone.`)) return

    try {
      const res = await fetch(`/api/resumes/${id}`, { method: 'DELETE' })
      if (res.status === 204) {
        showToast(`Deleted resume "${filename}"`, 'info')
        if (selectedResume?.id === id) setSelectedResume(null)
        setResumes((prev) => prev.filter((r) => r.id !== id))
      } else {
        showToast('Failed to delete resume', 'error')
      }
    } catch {
      showToast('Network error while deleting resume', 'error')
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-on-surface">
      {/* Top Navigation Bar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Workstation Container */}
      <main className="max-w-[1720px] w-full mx-auto px-margin-desktop py-6 flex-1 space-y-6">
        {activeTab === 'resumes' && (
          <>
            <ResumeUpload onUploadSuccess={handleUploadSuccess} showToast={showToast} />
            <ResumeList
              resumes={resumes}
              loading={loading}
              onRefresh={fetchResumes}
              onSelectResume={setSelectedResume}
              onDeleteResume={handleDeleteResume}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              showToast={showToast}
            />
          </>
        )}

        {activeTab === 'jds' && <JobDescriptions showToast={showToast} />}

        {activeTab === 'dashboard' && (
          <Dashboard
            resumes={resumes}
            onSelectResume={setSelectedResume}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'pipeline' && <PipelineOverview />}

        {/* Telemetry Footer */}
        <Footer />
      </main>

      {/* Candidate NER / JSON Details Modal */}
      {selectedResume && (
        <ResumeDetailModal
          resume={selectedResume}
          onClose={() => setSelectedResume(null)}
        />
      )}

      {/* Toast Notifications */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-body-sm font-body-sm border transition-all ${
              t.type === 'success'
                ? 'bg-surface-container-lowest border-emerald-400 text-emerald-900'
                : t.type === 'error'
                ? 'bg-surface-container-lowest border-error text-error'
                : 'bg-surface-container-lowest border-primary/50 text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">
              {t.type === 'success' ? 'check_circle' : t.type === 'error' ? 'error' : 'info'}
            </span>
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
