import { useEffect, useState } from 'react'

export default function Navbar({ activeTab, setActiveTab }) {
  const [health, setHealth] = useState({ status: 'checking', db: 'checking' })

  const checkHealth = async () => {
    try {
      const res = await fetch('/health')
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      } else {
        setHealth({ status: 'offline', db: 'disconnected' })
      }
    } catch {
      setHealth({ status: 'offline', db: 'disconnected' })
    }
  }

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [])

  const navItems = [
    { id: 'resumes',   icon: 'task_alt',    label: 'Resumes & Parsing' },
    { id: 'jds',       icon: 'work',        label: 'Job Descriptions' },
    { id: 'rankings',  icon: 'leaderboard', label: 'Rankings' },
    { id: 'fairness',  icon: 'balance',     label: 'Fairness Audit' },
    { id: 'dashboard', icon: 'query_stats', label: 'Dashboard' },
    { id: 'pipeline',  icon: 'hub',         label: 'Architecture' },
  ]

  return (
    <header className="docked full-width top-0 sticky z-50 bg-surface/90 border-b border-outline-variant/60 flex justify-between items-center w-full px-margin-desktop h-16 transition-all duration-150 backdrop-blur-md">
      {/* Brand / Phase Indicator */}
      <div className="flex items-center gap-space-md">
        <div className="w-10 h-10 rounded-xl bg-surface-container border border-outline-variant flex items-center justify-center text-primary shadow-sm">
          <span className="material-symbols-outlined text-[20px]">description</span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-title-lg font-title-lg font-bold tracking-tight text-on-surface">Chayankarta</span>
            <span className="text-label-sm font-label-sm px-2 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed-variant border border-outline-variant/80">
              PHASE 2
            </span>
          </div>
          <p className="text-label-md font-label-md text-on-surface-variant leading-none">
            चयनकर्ता · AI Candidate Ranking
          </p>
        </div>
      </div>

      {/* Centered Navigation Cluster */}
      <nav className="hidden md:flex items-center gap-6 h-full pt-4">
        {navItems.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setActiveTab(item.id)}
            className={`${
              activeTab === item.id
                ? 'text-primary border-b-2 border-primary font-semibold'
                : 'text-on-surface-variant hover:text-on-surface transition-colors'
            } pb-4 flex items-center gap-1.5 bg-transparent border-0 cursor-pointer text-xs`}
          >
            <span className="material-symbols-outlined text-[17px]">{item.icon}</span>
            <span className="font-label-md">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Trailing Actions & System Health */}
      <div className="flex items-center gap-space-md">
        {/* Real-time Live Connection Pill */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-low border border-outline-variant/70 text-label-md font-label-md">
          <span className="relative flex h-2 w-2">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                health.status === 'ok' ? 'bg-emerald-500' : health.status === 'checking' ? 'bg-amber-500' : 'bg-red-500'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                health.status === 'ok' ? 'bg-emerald-600' : health.status === 'checking' ? 'bg-amber-600' : 'bg-red-600'
              }`}
            />
          </span>
          <span className="text-on-surface font-medium">
            {health.status === 'ok' ? 'API Online' : health.status === 'checking' ? 'Connecting...' : 'API Offline'}
          </span>
          <span className="text-outline-variant">|</span>
          <span className="text-on-surface-variant text-label-sm font-label-sm">
            DB: {health.db === 'connected' ? 'OK' : '✗'}
          </span>
        </div>

        {/* Icon Actions */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors"
            title="System Active"
          >
            <span className="material-symbols-outlined text-[20px]">notifications</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('dashboard')}
            className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors"
            title="View Analytics & KPIs"
          >
            <span className="material-symbols-outlined text-[20px]">tune</span>
          </button>
        </div>

        {/* User Avatar */}
        <div className="flex items-center pl-2 border-l border-outline-variant">
          <div className="w-8 h-8 rounded-full bg-primary-fixed border border-outline-variant flex items-center justify-center text-primary text-xs font-bold ring-2 ring-primary/10 cursor-pointer">
            AI
          </div>
        </div>
      </div>
    </header>
  )
}
