import { useState, useEffect, useCallback } from 'react'

const API = '/api'

function MetricCard({ label, value, subtext, icon, color = 'text-primary', bgColor = 'bg-primary/10' }) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant/60 rounded-xl p-4 space-y-2">
      <div className="flex items-center gap-2">
        <div className={`w-8 h-8 rounded-lg ${bgColor} flex items-center justify-center`}>
          <span className={`material-symbols-outlined text-[18px] ${color}`}>{icon}</span>
        </div>
        <span className="text-label-sm text-on-surface-variant font-medium">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {subtext && <p className="text-xs text-on-surface-variant">{subtext}</p>}
    </div>
  )
}

function PassFailBadge({ passes }) {
  if (passes === null || passes === undefined) return null
  return passes ? (
    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 text-sm font-semibold">
      <span className="material-symbols-outlined text-[16px]">check_circle</span>
      PASS — 4/5 Rule
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-100 text-red-800 border border-red-200 text-sm font-semibold">
      <span className="material-symbols-outlined text-[16px]">cancel</span>
      FAIL — 4/5 Rule
    </span>
  )
}

function GroupBar({ group, maxRate }) {
  const pct = maxRate > 0 ? (group.selection_rate / maxRate) * 100 : 0
  const label = group.group_label.replace(/_/g, ' ')

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-on-surface capitalize">{label}</span>
        <div className="flex items-center gap-3 text-on-surface-variant text-xs">
          <span>n={group.count}</span>
          <span>μ={group.mean_score.toFixed(1)}</span>
          <span>σ={group.std_score.toFixed(1)}</span>
          <span className="font-semibold text-on-surface">{(group.selection_rate * 100).toFixed(1)}% selected</span>
        </div>
      </div>
      <div className="h-6 bg-surface-container rounded-lg overflow-hidden relative">
        <div
          className="h-full bg-primary rounded-lg transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-mono text-on-surface-variant">
          {(group.selection_rate * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  )
}

function RedactPreview({ resumeId, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/audit/redact-preview/${resumeId}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [resumeId])

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center modal-overlay p-4">
      <div className="bg-surface rounded-2xl border border-outline-variant w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-outline-variant">
          <div>
            <h3 className="text-title-md font-semibold text-on-surface">PII Redaction Preview</h3>
            {data && (
              <p className="text-xs text-on-surface-variant">
                {data.filename} — {data.redaction_count} items redacted
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-surface-container text-on-surface-variant"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="spinner" />
          </div>
        ) : data ? (
          <div className="flex-1 overflow-auto p-5 grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-semibold text-on-surface-variant uppercase mb-2">Original</p>
              <pre className="text-xs bg-surface-container rounded-lg p-3 whitespace-pre-wrap font-mono text-on-surface overflow-auto max-h-96">
                {data.original_text}
              </pre>
            </div>
            <div>
              <p className="text-xs font-semibold text-emerald-700 uppercase mb-2">Redacted (used for scoring)</p>
              <pre className="text-xs bg-emerald-50 border border-emerald-200 rounded-lg p-3 whitespace-pre-wrap font-mono text-on-surface overflow-auto max-h-96">
                {data.redacted_text}
              </pre>
            </div>
            {data.redacted_categories?.length > 0 && (
              <div className="col-span-2">
                <p className="text-xs font-semibold text-on-surface-variant mb-2">Redacted categories</p>
                <div className="flex gap-2 flex-wrap">
                  {data.redacted_categories.map((c) => (
                    <span key={c} className="px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-800 border border-amber-200">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-on-surface-variant text-sm">
            Could not load redaction preview.
          </div>
        )}
      </div>
    </div>
  )
}

export default function FairnessAudit({ showToast }) {
  const [jds, setJds] = useState([])
  const [selectedJdId, setSelectedJdId] = useState('')
  const [threshold, setThreshold] = useState(60)
  const [loading, setLoading] = useState(false)
  const [audit, setAudit] = useState(null)
  const [error, setError] = useState('')
  const [previewResumeId, setPreviewResumeId] = useState(null)
  const [resumes, setResumes] = useState([])

  useEffect(() => {
    fetch(`${API}/jds/?limit=50`)
      .then((r) => r.json())
      .then((d) => {
        setJds(d.job_descriptions || [])
        if (d.job_descriptions?.length > 0) setSelectedJdId(d.job_descriptions[0].id)
      })
      .catch(() => {})

    fetch(`${API}/resumes/?limit=100`)
      .then((r) => r.json())
      .then((d) => setResumes(d.resumes || []))
      .catch(() => {})
  }, [])

  const runAudit = useCallback(async () => {
    setLoading(true)
    setError('')
    setAudit(null)
    try {
      const params = new URLSearchParams({ threshold })
      if (selectedJdId) params.append('jd_id', selectedJdId)
      const res = await fetch(`${API}/audit/fairness?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setAudit(data)
      showToast('Fairness audit complete', 'success')
    } catch (err) {
      setError(err.message)
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [selectedJdId, threshold, showToast])

  const maxRate = audit?.groups?.reduce((m, g) => Math.max(m, g.selection_rate), 0) ?? 1

  return (
    <div className="space-y-6">
      {previewResumeId && (
        <RedactPreview resumeId={previewResumeId} onClose={() => setPreviewResumeId(null)} />
      )}

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-700">
          <span className="material-symbols-outlined text-[20px]">balance</span>
        </div>
        <div>
          <h1 className="text-title-lg font-title-lg font-bold text-on-surface">Fairness Audit</h1>
          <p className="text-label-md font-label-md text-on-surface-variant">
            Bias detection, PII redaction preview, and disparate impact analysis
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-surface-container-lowest border border-outline-variant/60 rounded-2xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 space-y-1">
            <label className="text-label-sm text-on-surface-variant font-medium">Job Description (optional)</label>
            <select
              value={selectedJdId}
              onChange={(e) => setSelectedJdId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">— First JD in DB —</option>
              {jds.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} {j.company ? `@ ${j.company}` : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-label-sm text-on-surface-variant font-medium">Selection Threshold (0–100)</label>
            <input
              type="number"
              min={0}
              max={100}
              step={5}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={runAudit}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-600 text-white text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {loading ? (
            <><div className="btn-spinner" /> Running Audit...</>
          ) : (
            <><span className="material-symbols-outlined text-[18px]">play_arrow</span> Run Fairness Audit</>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-2 text-red-700 text-sm">
          <span className="material-symbols-outlined text-[18px]">error</span>
          {error}
        </div>
      )}

      {/* Audit results */}
      {audit && (
        <div className="space-y-6">
          {/* Metric cards row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Total Candidates"
              value={audit.total_candidates}
              icon="groups"
              color="text-primary"
              bgColor="bg-primary/10"
            />
            <MetricCard
              label="Disparate Impact Ratio"
              value={audit.disparate_impact_ratio != null ? audit.disparate_impact_ratio.toFixed(3) : 'N/A'}
              subtext="≥ 0.80 = passes 4/5 rule"
              icon="analytics"
              color={audit.passes_four_fifths_rule === false ? 'text-red-600' : 'text-emerald-600'}
              bgColor={audit.passes_four_fifths_rule === false ? 'bg-red-100' : 'bg-emerald-100'}
            />
            <MetricCard
              label="Selection Threshold"
              value={`${audit.threshold}`}
              subtext="Score cutoff (0–100)"
              icon="filter_alt"
              color="text-amber-700"
              bgColor="bg-amber-100"
            />
            <MetricCard
              label="Score Δ (Redaction)"
              value={audit.score_delta_redaction != null ? `${audit.score_delta_redaction.toFixed(1)} pts` : 'N/A'}
              subtext="Mean abs change vs raw scoring"
              icon="swap_vert"
              color="text-violet-700"
              bgColor="bg-violet-100"
            />
          </div>

          {/* Pass/Fail badge + summary */}
          <div className="bg-surface-container-lowest border border-outline-variant/60 rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-3">
              <PassFailBadge passes={audit.passes_four_fifths_rule} />
              {audit.redaction_enabled && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-800 border border-blue-200 text-sm font-medium">
                  <span className="material-symbols-outlined text-[14px]">visibility_off</span>
                  PII Redaction Active
                </span>
              )}
            </div>
            {audit.summary && (
              <p className="text-sm text-on-surface-variant">{audit.summary}</p>
            )}
          </div>

          {/* Group comparison bar chart */}
          {audit.groups?.length > 0 && (
            <div className="bg-surface-container-lowest border border-outline-variant/60 rounded-xl p-5 space-y-4">
              <p className="text-label-md font-semibold text-on-surface">Group Selection Rates</p>
              <p className="text-xs text-on-surface-variant">
                Groups inferred from proxy signals in resume text (gender pronouns, institution tier).
                Candidate data is never directly solicited.
              </p>
              <div className="space-y-4">
                {audit.groups.map((g) => (
                  <GroupBar key={g.group_label} group={g} maxRate={maxRate} />
                ))}
              </div>
            </div>
          )}

          {/* Redaction preview table */}
          {resumes.length > 0 && (
            <div className="bg-surface-container-lowest border border-outline-variant/60 rounded-xl p-5 space-y-3">
              <p className="text-label-md font-semibold text-on-surface">PII Redaction Preview</p>
              <p className="text-xs text-on-surface-variant mb-3">
                Click any resume to see a side-by-side comparison of original vs redacted text.
              </p>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {resumes.slice(0, 20).map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setPreviewResumeId(r.id)}
                    className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-container transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px] text-on-surface-variant">description</span>
                    <span className="text-sm text-on-surface truncate">{r.filename}</span>
                    <span className="material-symbols-outlined text-[14px] text-primary ml-auto">preview</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!audit && !loading && !error && (
        <div className="text-center py-20 text-on-surface-variant">
          <span className="material-symbols-outlined text-5xl block mb-3 text-outline">balance</span>
          <p className="text-base font-medium">Run a fairness audit to detect potential bias</p>
          <p className="text-sm mt-1">Analyzes score distributions across inferred demographic groups</p>
        </div>
      )}
    </div>
  )
}
