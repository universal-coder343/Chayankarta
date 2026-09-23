import { useState } from 'react'

export default function ResumeDetailModal({ resume, onClose }) {
  const [activeTab, setActiveTab] = useState('entities') // 'entities', 'json', 'raw_text'

  if (!resume) return null

  const ner = resume.ner || {}
  const candidate = ner.candidate_name || 'Candidate Details'
  const contact = ner.contact_info || {}
  const emails = contact.emails || []
  const phones = contact.phones || []
  const urls = contact.urls || []
  const location = contact.location || null

  const skillsCategorized = ner.skills_categorized || {}
  const allSkills = ner.skills_all || []
  const experience = ner.experience || {}
  const education = ner.education || {}

  const categoryLabels = {
    languages: { name: 'Programming Languages', color: 'primary' },
    frameworks: { name: 'Frameworks & Libraries', color: 'secondary' },
    databases: { name: 'Databases & Storage', color: 'tertiary' },
    devops_cloud: { name: 'DevOps & Cloud', color: 'primary-container' },
    tools_platforms: { name: 'Tools & Platforms', color: 'secondary-container' },
    methodologies: { name: 'Methodologies & Concepts', color: 'outline' },
  }

  return (
    <div
      className="fixed inset-0 bg-inverse-surface/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 modal-overlay"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] flex flex-col bg-surface-container-lowest rounded-2xl border border-outline-variant/90 shadow-2xl overflow-hidden text-on-surface"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="flex items-center justify-between p-6 border-b border-outline-variant/70 bg-surface-container-low/60">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary-fixed border border-primary/30 flex items-center justify-center text-primary font-bold text-headline-sm">
              <span className="material-symbols-outlined text-[24px]">description</span>
            </div>
            <div>
              <h2 className="text-headline-sm font-headline-sm text-on-surface font-bold">{candidate}</h2>
              <p className="text-body-sm font-body-sm text-on-surface-variant font-code-metric">
                {resume.filename} &bull; {resume.file_type?.toUpperCase()} &bull; Method: {resume.parsing_method}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <span className="material-symbols-outlined text-[22px]">close</span>
          </button>
        </div>

        {/* Modal Tabs */}
        <div className="flex items-center gap-6 px-6 border-b border-outline-variant/60 bg-surface-container-lowest">
          <button
            type="button"
            onClick={() => setActiveTab('entities')}
            className={`py-3 text-label-md font-label-md flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
              activeTab === 'entities'
                ? 'border-primary text-primary'
                : 'border-transparent text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">verified</span>
            Extracted Entities &amp; Skills ({allSkills.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('json')}
            className={`py-3 text-label-md font-label-md flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
              activeTab === 'json'
                ? 'border-primary text-primary'
                : 'border-transparent text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">data_object</span>
            Parsed JSON (NER Schema)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('raw_text')}
            className={`py-3 text-label-md font-label-md flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
              activeTab === 'raw_text'
                ? 'border-primary text-primary'
                : 'border-transparent text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">notes</span>
            Raw Extracted Text
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {activeTab === 'entities' && (
            <div className="space-y-6">
              {/* Contact Information */}
              <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-3">
                <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-primary">contacts</span>
                  Candidate Contact Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-body-sm font-body-sm">
                  <div>
                    <span className="text-label-sm font-label-sm text-outline uppercase block">Candidate Name:</span>
                    <span className="text-on-surface font-semibold text-body-md">{candidate}</span>
                  </div>
                  <div>
                    <span className="text-label-sm font-label-sm text-outline uppercase block">Location:</span>
                    <span className="text-on-surface">{location || 'None extracted'}</span>
                  </div>
                  <div>
                    <span className="text-label-sm font-label-sm text-outline uppercase block">Email Address:</span>
                    <span className="text-on-surface font-code-metric">{emails.length ? emails.join(', ') : 'None extracted'}</span>
                  </div>
                  <div>
                    <span className="text-label-sm font-label-sm text-outline uppercase block">Phone:</span>
                    <span className="text-on-surface font-code-metric">{phones.length ? phones.join(', ') : 'None extracted'}</span>
                  </div>
                  {urls.length > 0 && (
                    <div className="md:col-span-2">
                      <span className="text-label-sm font-label-sm text-outline uppercase block">Profile URLs:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {urls.map((u, idx) => (
                          <a
                            key={idx}
                            href={u.startsWith('http') ? u : `https://${u}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-primary hover:underline font-code-metric text-[12px]"
                          >
                            {u}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Experience & Education Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-3">
                  <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px] text-secondary">work_history</span>
                    Work Experience
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className="text-headline-md font-headline-md text-secondary font-bold font-code-metric">
                      {experience.total_years_est ?? 'N/A'}
                    </span>
                    <span className="text-body-sm font-body-sm text-on-surface-variant">years estimated</span>
                  </div>
                  {experience.job_titles?.length > 0 && (
                    <div>
                      <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">Detected Roles:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {experience.job_titles.map((t, i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-primary-fixed text-primary font-medium">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-3">
                  <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px] text-emerald-800">school</span>
                    Education
                  </h3>
                  {education.degrees?.length > 0 ? (
                    <div>
                      <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">Degrees:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {education.degrees.map((d, i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-lowest border border-outline-variant text-on-surface font-medium">
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-body-sm font-body-sm text-on-surface-variant italic">No degrees explicitly matched.</p>
                  )}
                  {education.institutions?.length > 0 && (
                    <div>
                      <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">Institutions:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {education.institutions.map((inst, i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-lowest text-on-surface-variant">
                            {inst}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Categorized Skills Taxonomy */}
              <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-4">
                <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-primary">psychology</span>
                  Extracted Skills Taxonomy ({allSkills.length} Total)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(skillsCategorized).map(([catKey, skills]) => {
                    if (!skills || !skills.length) return null
                    const meta = categoryLabels[catKey] || { name: catKey }
                    return (
                      <div key={catKey} className="p-3 rounded-lg bg-surface-container-lowest border border-outline-variant/60">
                        <span className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider block mb-2 font-semibold">
                          {meta.name} ({skills.length})
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {skills.map((s, idx) => (
                            <span key={idx} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-primary-fixed border border-primary/25 text-primary font-medium">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'json' && (
            <div className="p-4 rounded-xl bg-inverse-surface text-inverse-on-surface font-code-md text-[12px] overflow-x-auto shadow-inner">
              <pre>{JSON.stringify(resume, null, 2)}</pre>
            </div>
          )}

          {activeTab === 'raw_text' && (
            <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/80 font-code-md text-on-surface text-[12px] whitespace-pre-wrap leading-relaxed shadow-inner">
              {resume.raw_text || 'No raw text extracted.'}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-outline-variant/70 bg-surface-container-low/40 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-semibold text-label-md font-label-md transition-colors shadow-sm"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
