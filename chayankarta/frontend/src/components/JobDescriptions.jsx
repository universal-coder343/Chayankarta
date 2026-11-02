import { useState, useEffect } from 'react'

const SAMPLE_JDS = [
  {
    name: 'Senior ML Engineer',
    title: 'Senior Machine Learning Engineer',
    company: 'DeepTech Innovations',
    raw_text: `Role: Senior Machine Learning Engineer
Company: DeepTech Innovations
Location: San Francisco, CA (Hybrid)

About the Role:
We are seeking an experienced ML Engineer to build cutting-edge resume screening and entity extraction pipelines using modern NLP architectures.

Required Skills & Experience:
- 5+ years of software engineering experience with strong proficiency in Python and PyTorch.
- Hands-on experience with NLP pipelines: spaCy, Transformers, Sentence-BERT, vector databases.
- Strong knowledge of Docker, Kubernetes, MLOps, and REST APIs.
- Bachelor's or Master's in Computer Science, Data Science, or related field.

Preferred Skills:
- Experience with OCR frameworks (Tesseract OCR, AWS Textract).
- Experience building fair, bias-audited candidate evaluation algorithms.`,
  },
  {
    name: 'Full Stack Cloud Architect',
    title: 'Full Stack Cloud Architect',
    company: 'Nexus Software Labs',
    raw_text: `Role: Full Stack Cloud Architect
Company: Nexus Software Labs
Location: Austin, TX

Key Responsibilities:
- Build reactive, high-performance web user interfaces using React, TypeScript, and Tailwind.
- Develop distributed backend services with Go (Golang), Python FastAPI, and MongoDB.
- Architect cloud infrastructure using AWS Lambda, Redis, GraphQL, and CI/CD pipelines.

Qualifications:
- Bachelor's in Software Engineering or equivalent experience.
- 5+ years building scalable cloud applications.
- Strong proficiency in React, TypeScript, Go, AWS, and Docker.`,
  },
]

export default function JobDescriptions({ showToast }) {
  const [jds, setJds] = useState([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [rawText, setRawText] = useState('')
  const [selectedJd, setSelectedJd] = useState(null)

  const fetchJds = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/jds/?limit=50')
      if (res.ok) {
        const data = await res.json()
        setJds(data.job_descriptions || [])
      }
    } catch {
      showToast('Could not load job descriptions.', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJds()
  }, [])

  const handleLoadSample = (sample) => {
    setTitle(sample.title)
    setCompany(sample.company)
    setRawText(sample.raw_text)
    showToast(`Loaded sample position: ${sample.name}`, 'info')
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!title.trim() || !rawText.trim()) {
      showToast('Title and Requirements text are required.', 'error')
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch('/api/jds/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          company: company.trim() || null,
          raw_text: rawText.trim(),
        }),
      })

      if (res.status === 201) {
        const created = await res.json()
        showToast(`Job Position "${created.title}" analyzed & saved!`, 'success')
        setTitle('')
        setCompany('')
        setRawText('')
        fetchJds()
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err.detail || 'Failed to parse Job Description', 'error')
      }
    } catch {
      showToast('Network error connecting to API.', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id, jdTitle) => {
    if (!window.confirm(`Delete position "${jdTitle}"?`)) return
    try {
      const res = await fetch(`/api/jds/${id}`, { method: 'DELETE' })
      if (res.status === 204) {
        showToast(`Deleted "${jdTitle}"`, 'info')
        if (selectedJd?.id === id) setSelectedJd(null)
        setJds(jds.filter((j) => j.id !== id))
      } else {
        showToast('Failed to delete Job Description', 'error')
      }
    } catch {
      showToast('Error deleting Job Description', 'error')
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Create Form */}
        <div className="lg:col-span-5 rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 warm-card-shadow space-y-4">
          <div>
            <h2 className="text-headline-sm font-headline-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[22px]">post_add</span>
              Parse Job Description
            </h2>
            <p className="text-body-sm font-body-sm text-on-surface-variant mt-1">
              Extract required &amp; preferred skill constraints, minimum experience, and degree qualifications.
            </p>
          </div>

          {/* Quick Sample Selector */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-label-sm font-label-sm text-outline uppercase font-semibold">Templates:</span>
            {SAMPLE_JDS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleLoadSample(s)}
                className="px-2.5 py-1 rounded-md text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-on-surface hover:border-primary transition-colors"
              >
                + {s.name}
              </button>
            ))}
          </div>

          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label htmlFor="jd-title" className="block text-label-sm font-label-sm text-outline uppercase mb-1">
                Position Title *
              </label>
              <input
                id="jd-title"
                type="text"
                required
                placeholder="e.g. Senior Machine Learning Engineer"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant/80 rounded-lg px-3 py-2 text-body-md text-on-surface focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label htmlFor="jd-company" className="block text-label-sm font-label-sm text-outline uppercase mb-1">
                Company / Organization
              </label>
              <input
                id="jd-company"
                type="text"
                placeholder="e.g. DeepTech Innovations"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant/80 rounded-lg px-3 py-2 text-body-md text-on-surface focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label htmlFor="jd-text" className="block text-label-sm font-label-sm text-outline uppercase mb-1">
                Job Requirements Text *
              </label>
              <textarea
                id="jd-text"
                required
                rows={8}
                placeholder="Paste the full job requirements, skills, experience, and educational criteria..."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant/80 rounded-lg p-3 text-body-sm text-on-surface focus:outline-none focus:border-primary font-body-sm custom-scrollbar"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-semibold text-label-md font-label-md transition-colors flex items-center justify-center gap-2 shadow-sm"
            >
              {submitting ? (
                <>
                  <span className="btn-spinner"></span>
                  <span>Extracting Requirements...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">psychology</span>
                  <span>Analyze &amp; Save Job Description</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right: Saved Position Dossiers */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-headline-sm font-headline-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[22px]">work</span>
              Active Target Positions ({jds.length})
            </h2>
            <button
              type="button"
              onClick={fetchJds}
              className="p-1.5 text-on-surface-variant hover:text-on-surface rounded-lg bg-surface-container-low border border-outline-variant hover:border-outline transition-colors"
              title="Refresh positions"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
            </button>
          </div>

          {loading ? (
            <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-8 text-center">
              <div className="spinner mx-auto mb-2"></div>
              <p className="text-body-sm text-on-surface-variant">Loading job descriptions...</p>
            </div>
          ) : jds.length === 0 ? (
            <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-8 text-center warm-card-shadow">
              <span className="material-symbols-outlined text-[36px] text-outline mb-1">work_outline</span>
              <p className="text-body-md text-on-surface font-semibold">No active job descriptions</p>
              <p className="text-body-sm text-on-surface-variant mt-1">
                Create a position or click one of the quick templates on the left.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {jds.map((jd) => {
                const ner = jd.ner || {}
                const reqSkills = ner.required_skills || []
                const prefSkills = ner.preferred_skills || []
                const expYears = ner.experience_required_years || {}
                const isSelected = selectedJd?.id === jd.id

                return (
                  <div
                    key={jd.id}
                    onClick={() => setSelectedJd(isSelected ? null : jd)}
                    className={`rounded-xl bg-surface-container-lowest border-2 ${
                      isSelected ? 'border-primary' : 'border-outline-variant/80 hover:border-outline'
                    } p-5 cursor-pointer transition-all warm-card-shadow`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-headline-sm font-headline-sm text-on-surface font-bold">
                          {jd.title}
                        </h3>
                        <p className="text-label-md font-label-md text-primary font-medium">
                          {jd.company || 'Direct Requisition'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(jd.id, jd.title)
                        }}
                        className="text-on-surface-variant hover:text-error p-1 transition-colors"
                        title="Delete position"
                      >
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 mt-3 text-label-sm font-label-sm">
                      {expYears.min !== null && expYears.min !== undefined && (
                        <span className="px-2.5 py-0.5 rounded bg-surface-container-low border border-outline-variant text-on-surface font-medium">
                          {expYears.min}{expYears.max ? ` - ${expYears.max}` : '+'} years exp
                        </span>
                      )}
                      {ner.education_required?.length > 0 && (
                        <span className="px-2.5 py-0.5 rounded bg-emerald-50 border border-emerald-300 text-emerald-800 font-medium">
                          {ner.education_required.join(', ')}
                        </span>
                      )}
                    </div>

                    {reqSkills.length > 0 && (
                      <div className="mt-3">
                        <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">
                          Required Skill Entities ({reqSkills.length}):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {reqSkills.map((s, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-primary-fixed border border-primary/25 text-primary font-medium"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {prefSkills.length > 0 && (
                      <div className="mt-2">
                        <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">
                          Preferred Competencies:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {prefSkills.map((s, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-secondary-fixed/60 border border-secondary/30 text-secondary font-medium"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {isSelected && (
                      <div className="mt-4 pt-3 border-t border-outline-variant/60">
                        <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">Raw Job Description:</span>
                        <pre className="p-3 rounded-lg bg-surface-container-low text-[12px] font-code-md text-on-surface whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto custom-scrollbar">
                          {jd.raw_text}
                        </pre>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
