import { useState } from 'react'

export default function ResumeDetailModal({ resume, onClose }) {
  const [activeTab, setActiveTab] = useState('entities')

  if (!resume) return null

  const ner = resume.ner || {}

  // ── Normalise flat backend schema (name/email/phone/skills/education/experience)
  // to what the UI needs, while staying compatible if the schema changes.
  const candidate = ner.name || ner.candidate_name || 'Unknown Candidate'

  const emails   = ner.email   ? [ner.email]   : (ner.contact_info?.emails  || [])
  const phones   = ner.phone   ? [ner.phone]   : (ner.contact_info?.phones  || [])
  const urls     = ner.contact_info?.urls || []
  const location = ner.contact_info?.location  || null

  // skills — backend sends a flat array
  const allSkills = Array.isArray(ner.skills) ? ner.skills
                  : Array.isArray(ner.skills_all) ? ner.skills_all
                  : []

  // experience — backend sends a list of strings or an object
  const experienceLines = Array.isArray(ner.experience) ? ner.experience : []
  const experienceYears = typeof ner.experience === 'object' && !Array.isArray(ner.experience)
                          ? (ner.experience?.total_years_est ?? null)
                          : null
  const jobTitles = typeof ner.experience === 'object' && !Array.isArray(ner.experience)
                    ? (ner.experience?.job_titles || [])
                    : []

  // education — backend sends a list of degree strings or an object
  const educationDegrees = Array.isArray(ner.education)
                           ? ner.education
                           : (ner.education?.degrees || [])
  const educationInstitutions = Array.isArray(ner.education)
                                 ? []
                                 : (ner.education?.institutions || [])

  const certifications = ner.certifications || []

  return (
    <div
      className="fixed inset-0 bg-inverse-surface/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 modal-overlay"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] flex flex-col bg-surface-container-lowest rounded-2xl border border-outline-variant/90 shadow-2xl overflow-hidden text-on-surface"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Header ── */}
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

        {/* ── Tabs ── */}
        <div className="flex items-center gap-6 px-6 border-b border-outline-variant/60 bg-surface-container-lowest">
          {[
            { id: 'entities', icon: 'verified',    label: `Extracted Entities & Skills (${allSkills.length})` },
            { id: 'json',     icon: 'data_object', label: 'Parsed JSON (NER Schema)' },
            { id: 'raw_text', icon: 'notes',       label: 'Raw Extracted Text' },
          ].map(({ id, icon, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`py-3 text-label-md font-label-md flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
                activeTab === id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">{icon}</span>
              {label}
            </button>
          ))}
        </div>

        {/* ── Body ── */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">

          {/* ── Entities tab ── */}
          {activeTab === 'entities' && (
            <div className="space-y-6">

              {/* Contact */}
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
                    <span className="text-on-surface font-code-metric">
                      {emails.length ? emails.join(', ') : 'None extracted'}
                    </span>
                  </div>
                  <div>
                    <span className="text-label-sm font-label-sm text-outline uppercase block">Phone:</span>
                    <span className="text-on-surface font-code-metric">
                      {phones.length ? phones.join(', ') : 'None extracted'}
                    </span>
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

              {/* Experience & Education */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Experience */}
                <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-3">
                  <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px] text-secondary">work_history</span>
                    Work Experience
                  </h3>
                  {experienceYears !== null ? (
                    <div className="flex items-center gap-2">
                      <span className="text-headline-md font-headline-md text-secondary font-bold font-code-metric">
                        {experienceYears}
                      </span>
                      <span className="text-body-sm font-body-sm text-on-surface-variant">years estimated</span>
                    </div>
                  ) : null}
                  {jobTitles.length > 0 && (
                    <div>
                      <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">Detected Roles:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {jobTitles.map((t, i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-primary-fixed text-primary font-medium">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {experienceLines.length > 0 && (
                    <ul className="text-body-sm font-body-sm text-on-surface-variant space-y-1 list-disc list-inside">
                      {experienceLines.map((line, i) => (
                        <li key={i}>{line}</li>
                      ))}
                    </ul>
                  )}
                  {experienceYears === null && jobTitles.length === 0 && experienceLines.length === 0 && (
                    <p className="text-body-sm font-body-sm text-on-surface-variant italic">No experience data extracted.</p>
                  )}
                </div>

                {/* Education */}
                <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-3">
                  <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px] text-emerald-800">school</span>
                    Education
                  </h3>
                  {educationDegrees.length > 0 ? (
                    <div>
                      <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">Degrees:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {educationDegrees.map((d, i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-lowest border border-outline-variant text-on-surface font-medium">
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-body-sm font-body-sm text-on-surface-variant italic">No degrees explicitly matched.</p>
                  )}
                  {educationInstitutions.length > 0 && (
                    <div>
                      <span className="text-label-sm font-label-sm text-outline uppercase block mb-1">Institutions:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {educationInstitutions.map((inst, i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-lowest text-on-surface-variant">
                            {inst}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Skills */}
              <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-4">
                <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-primary">psychology</span>
                  Extracted Skills ({allSkills.length} Total)
                </h3>
                {allSkills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {allSkills.map((s, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-primary-fixed border border-primary/25 text-primary font-medium">
                        {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-body-sm font-body-sm text-on-surface-variant italic">No skills matched from taxonomy.</p>
                )}
              </div>

              {/* Certifications */}
              {certifications.length > 0 && (
                <div className="p-5 rounded-xl bg-surface-container-low border border-outline-variant/70 space-y-3">
                  <h3 className="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px] text-tertiary">verified_user</span>
                    Certifications
                  </h3>
                  <ul className="text-body-sm font-body-sm text-on-surface space-y-1 list-disc list-inside">
                    {certifications.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* ── JSON tab ── */}
          {activeTab === 'json' && (
            <div className="p-4 rounded-xl bg-inverse-surface text-inverse-on-surface font-code-md text-[12px] overflow-x-auto shadow-inner">
              <pre>{JSON.stringify(resume, null, 2)}</pre>
            </div>
          )}

          {/* ── Raw text tab ── */}
          {activeTab === 'raw_text' && (
            <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/80 font-code-md text-on-surface text-[12px] whitespace-pre-wrap leading-relaxed shadow-inner">
              {resume.raw_text || 'No raw text extracted.'}
            </div>
          )}
        </div>

        {/* ── Footer ── */}
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
