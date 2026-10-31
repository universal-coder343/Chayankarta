import { useState, useEffect, useCallback } from 'react'

const API = '/api'

function SkillChip({ label, variant = 'matched' }) {
  const colors = {
    matched: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    missing: 'bg-red-50 text-red-700 border-red-200',
    preferred: 'bg-blue-50 text-blue-700 border-blue-200',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${colors[variant]}`}>
      {label}
    </span>
  )
}

function ScoreBar({ label, score, color = 'bg-primary', weight }) {
  const pct = Math.round(score * 100)
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-32 text-on-surface-variant truncate">{label}</span>
      <div className="flex-1 bg-surface-container rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right font-mono text-on-surface">{pct}%</span>
      {weight != null && (
        <span className="text-outline-variant">×{weight}</span>
      )}
    </div>
  )
}

function CandidateRow({ candidate, rank, isExpanded, onToggle }) {
  const { breakdown } = candidate
  const scoreColor =
    candidate.final_score >= 70
      ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
      : candidate.final_score >= 45
      ? 'text-amber-700 bg-amber-50 border-amber-200'
      : 'text-red-700 bg-red-50 border-red-200'

  return (
    <div className="border border-outline-variant/60 rounded-xl overflow-hidden">
      {/* Header row */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-4 px-4 py-3 bg-surface hover:bg-surface-container/50 transition-colors text-left"
      >
        {/* Rank badge */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
          rank === 1 ? 'bg-amber-400 text-amber-900' :
          rank === 2 ? 'bg-slate-300 text-slate-700' :
          rank === 3 ? 'bg-orange-300 text-orange-800' :
          'bg-surface-container text-on-surface-variant'
        }`}>
          {rank}
        </div>

        {/* Name + file */}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-on-surface truncate">
            {candidate.candidate_name || candidate.filename}
          </div>
          {candidate.candidate_name && (
            <div className="text-xs text-on-surface-variant truncate">{candidate.filename}</div>
          )}
        </div>

        {/* Score pill */}
        <div className={`px-3 py-1 rounded-full text-sm font-bold border ${scoreColor}`}>
          {candidate.final_score.toFixed(1)}
        </div>

        {/* Top matched skills chips */}
        <div className="hidden lg:flex gap-1 flex-wrap max-w-xs">
          {breakdown.matched_skills.slice(0, 3).map((s) => (
            <SkillChip key={s} label={s} variant="matched" />
          ))}
          {breakdown.matched_skills.length > 3 && (
            <span className="text-xs text-on-surface-variant self-center">
              +{breakdown.matched_skills.length - 3}
            </span>
          )}
        </div>

        {/* Expand icon */}
        <span className="material-symbols-outlined text-[20px] text-on-surface-variant shrink-0">
          {isExpanded ? 'expand_less' : 'expand_more'}
        </span>
      </button>

      {/* Expanded breakdown */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 bg-surface-container/30 border-t border-outline-variant/40 space-y-4">
          {/* Explanation */}
          {candidate.explanation && (
            <p className="text-sm text-on-surface-variant italic">{candidate.explanation}</p>
          )}

          {/* Score bars */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-on-surface uppercase tracking-wider">Score Breakdown</p>
            <ScoreBar label="Semantic Similarity" score={breakdown.semantic_score} color="bg-violet-500" weight="0.40" />
            <ScoreBar label="Skill Match" score={breakdown.skill_overlap_score} color="bg-primary" weight="0.35" />
            <ScoreBar label="Experience" score={breakdown.experience_score} color="bg-amber-500" weight="0.15" />
            <ScoreBar label="Education" score={breakdown.education_score} color="bg-emerald-500" weight="0.10" />
          </div>

          {/* Skills */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {breakdown.matched_skills.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-emerald-700 mb-1">✓ Matched Required</p>
                <div className="flex flex-wrap gap-1">
                  {breakdown.matched_skills.map((s) => <SkillChip key={s} label={s} variant="matched" />)}
                </div>
              </div>
            )}
            {breakdown.missing_skills.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-red-700 mb-1">✗ Missing Required</p>
                <div className="flex flex-wrap gap-1">
                  {breakdown.missing_skills.map((s) => <SkillChip key={s} label={s} variant="missing" />)}
                </div>
              </div>
            )}
            {breakdown.preferred_matched?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-blue-700 mb-1">★ Preferred Matched</p>
                <div className="flex flex-wrap gap-1">
                  {breakdown.preferred_matched.map((s) => <SkillChip key={s} label={s} variant="preferred" />)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Rankings({ showToast }) {
  const [jds, setJds] = useState([])
  const [selectedJdId, setSelectedJdId] = useState('')
  const [topK, setTopK] = useState(10)
  const [minScore, setMinScore] = useState(0)
  const [skillFilter, setSkillFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [rankResponse, setRankResponse] = useState(null)
  const [expandedId, setExpandedId] = useState(null)
  const [error, setError] = useState('')

  // Fetch JDs for the selector
  useEffect(() => {
    fetch(`${API}/jds/?limit=50`)
      .then((r) => r.json())
      .then((d) => {
        setJds(d.job_descriptions || [])
        if (d.job_descriptions?.length > 0) {
          setSelectedJdId(d.job_descriptions[0].id)
        }
      })
      .catch(() => {})
  }, [])

  const runRanking = useCallback(async () => {
    if (!selectedJdId) {
      showToast('Select a job description first', 'error')
      return
    }
    setLoading(true)
    setError('')
    setRankResponse(null)
    try {
      const res = await fetch(`${API}/rankings/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jd_id: selectedJdId, top_k: topK, min_score: minScore }),
      })
      if (!res.ok) {
        const detail = await res.json()
        throw new Error(detail.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setRankResponse(data)
      showToast(`Ranked ${data.total_resumes_evaluated} candidates`, 'success')
    } catch (err) {
      setError(err.message)
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [selectedJdId, topK, minScore, showToast])

  // Filter by skill keyword
  const filteredRankings = rankResponse?.rankings?.filter((r) => {
    if (!skillFilter) return true
    const q = skillFilter.toLowerCase()
    const allSkills = [
      ...(r.breakdown.matched_skills || []),
      ...(r.breakdown.missing_skills || []),
      ...(r.breakdown.preferred_matched || []),
    ]
    return allSkills.some((s) => s.toLowerCase().includes(q))
  }) ?? []

  const selectedJd = jds.find((j) => j.id === selectedJdId)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-violet-100 border border-violet-200 flex items-center justify-center text-violet-700">
          <span className="material-symbols-outlined text-[20px]">leaderboard</span>
        </div>
        <div>
          <h1 className="text-title-lg font-title-lg font-bold text-on-surface">Candidate Rankings</h1>
          <p className="text-label-md font-label-md text-on-surface-variant">
            Hybrid semantic + skill + experience + education scoring
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-surface-container-lowest border border-outline-variant/60 rounded-2xl p-5 space-y-4">
        <p className="text-label-md font-semibold text-on-surface">Ranking Configuration</p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* JD selector */}
          <div className="md:col-span-2 space-y-1">
            <label className="text-label-sm text-on-surface-variant font-medium">Job Description</label>
            <select
              value={selectedJdId}
              onChange={(e) => setSelectedJdId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">— Select a JD —</option>
              {jds.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} {j.company ? `@ ${j.company}` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Top K */}
          <div className="space-y-1">
            <label className="text-label-sm text-on-surface-variant font-medium">Top K</label>
            <input
              type="number"
              min={1}
              max={200}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>

          {/* Min score */}
          <div className="space-y-1">
            <label className="text-label-sm text-on-surface-variant font-medium">Min Score (0–100)</label>
            <input
              type="number"
              min={0}
              max={100}
              step={5}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant bg-surface text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={runRanking}
          disabled={loading || !selectedJdId}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-on-primary text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {loading ? (
            <>
              <div className="btn-spinner" />
              Ranking...
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-[18px]">play_arrow</span>
              Run Ranking
            </>
          )}
        </button>
      </div>

      {/* JD Info strip */}
      {selectedJd && (
        <div className="bg-violet-50 border border-violet-200 rounded-xl px-4 py-3 flex items-start gap-3">
          <span className="material-symbols-outlined text-violet-600 text-[18px] mt-0.5">work</span>
          <div>
            <p className="text-sm font-semibold text-violet-900">{selectedJd.title}</p>
            {selectedJd.company && <p className="text-xs text-violet-700">{selectedJd.company}</p>}
            {selectedJd.ner?.required_skills?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {selectedJd.ner.required_skills.slice(0, 8).map((s) => (
                  <SkillChip key={s} label={s} variant="matched" />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-2 text-red-700 text-sm">
          <span className="material-symbols-outlined text-[18px]">error</span>
          {error}
        </div>
      )}

      {/* Results */}
      {rankResponse && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-on-surface">
                {rankResponse.total_resumes_evaluated} candidates evaluated
                {rankResponse.redaction_enabled && (
                  <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200 font-medium">
                    PII Redaction ON
                  </span>
                )}
              </p>
              <p className="text-xs text-on-surface-variant">
                Weights: Semantic {(rankResponse.weights_used.semantic * 100).toFixed(0)}% ·
                Skill {(rankResponse.weights_used.skill_overlap * 100).toFixed(0)}% ·
                Exp {(rankResponse.weights_used.experience * 100).toFixed(0)}% ·
                Edu {(rankResponse.weights_used.education * 100).toFixed(0)}%
              </p>
            </div>

            {/* Skill filter */}
            <div className="relative">
              <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant">
                filter_list
              </span>
              <input
                type="text"
                placeholder="Filter by skill..."
                value={skillFilter}
                onChange={(e) => setSkillFilter(e.target.value)}
                className="pl-7 pr-3 py-1.5 text-sm rounded-lg border border-outline-variant bg-surface text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          {/* Empty after filter */}
          {filteredRankings.length === 0 && (
            <div className="text-center py-12 text-on-surface-variant">
              <span className="material-symbols-outlined text-4xl block mb-2">search_off</span>
              <p className="text-sm">No candidates match your filter criteria.</p>
            </div>
          )}

          {/* Candidate list */}
          <div className="space-y-2">
            {filteredRankings.map((candidate) => (
              <CandidateRow
                key={candidate.resume_id}
                candidate={candidate}
                rank={candidate.rank}
                isExpanded={expandedId === candidate.resume_id}
                onToggle={() =>
                  setExpandedId(expandedId === candidate.resume_id ? null : candidate.resume_id)
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!rankResponse && !loading && !error && (
        <div className="text-center py-20 text-on-surface-variant">
          <span className="material-symbols-outlined text-5xl block mb-3 text-outline">leaderboard</span>
          <p className="text-base font-medium">Select a job description and click Run Ranking</p>
          <p className="text-sm mt-1">Candidates will be scored and ranked by AI</p>
        </div>
      )}
    </div>
  )
}
