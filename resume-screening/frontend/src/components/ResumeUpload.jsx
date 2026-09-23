import { useState, useRef } from 'react'

export default function ResumeUpload({ onUploadSuccess, showToast }) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file) => {
    const validExtensions = ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!validExtensions.includes(ext)) {
      showToast(`Unsupported file type (${ext}). Please upload a PDF, DOCX, or Image file.`, 'error')
      return
    }
    setSelectedFile(file)
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const res = await fetch('/api/resumes/upload', {
        method: 'POST',
        body: formData,
      })

      if (res.status === 201) {
        const data = await res.json()
        showToast(`Successfully parsed and indexed "${selectedFile.name}"!`, 'success')
        setSelectedFile(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
        onUploadSuccess(data)
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err.detail || 'Failed to upload and parse resume', 'error')
      }
    } catch {
      showToast('Network error while connecting to the resume parsing service.', 'error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <section className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 relative overflow-hidden warm-card-shadow">
      <div className="absolute top-0 right-0 w-96 h-48 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>

      {/* Header & Parsing Engine Badges */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <h1 className="text-headline-md font-headline-md text-on-surface flex items-center gap-2">
            Upload &amp; Extract Resume
            <span className="material-symbols-outlined text-primary text-[22px]">psychology</span>
          </h1>
          <p className="text-body-md font-body-md text-on-surface-variant mt-1">
            Extract candidate entities, categorized skills, work experience, and education via NLP &amp; OCR pipeline.
          </p>
        </div>

        {/* Engines Indicators */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-primary font-medium">
            <span className="material-symbols-outlined text-[14px]">picture_as_pdf</span>
            PDF (pdfplumber)
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-secondary font-medium">
            <span className="material-symbols-outlined text-[14px]">article</span>
            DOCX (python-docx)
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-tertiary font-medium">
            <span className="material-symbols-outlined text-[14px]">document_scanner</span>
            Scanned (Tesseract OCR)
          </span>
        </div>
      </div>

      {/* Interactive Drop Zone */}
      <div
        className={`border-2 border-dashed ${
          dragActive
            ? 'border-primary bg-surface-container'
            : selectedFile
            ? 'border-emerald-600 bg-surface-container-low'
            : 'border-[#DDD5C7] hover:border-primary bg-surface-container-low/50 hover:bg-surface-container-low'
        } rounded-xl p-8 text-center transition-all duration-200 cursor-pointer group relative z-10`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.tiff,.bmp"
          onChange={handleChange}
          style={{ display: 'none' }}
          disabled={uploading}
        />

        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-surface-container-lowest border border-outline-variant/70 group-hover:border-primary/40 group-hover:bg-primary-fixed/40 flex items-center justify-center text-primary transition-all shadow-sm">
          {uploading ? (
            <div className="spinner"></div>
          ) : selectedFile ? (
            <span className="material-symbols-outlined text-[28px] text-emerald-700">check_circle</span>
          ) : (
            <span className="material-symbols-outlined text-[28px] group-hover:-translate-y-0.5 transition-transform">
              upload
            </span>
          )}
        </div>

        {selectedFile ? (
          <div className="space-y-1">
            <p className="text-body-lg font-body-lg text-on-surface font-semibold">
              {selectedFile.name}
            </p>
            <p className="text-body-sm font-body-sm text-emerald-700 font-medium font-code-metric">
              {(selectedFile.size / 1024).toFixed(1)} KB &bull; Ready for spaCy NER &amp; OCR analysis
            </p>
          </div>
        ) : (
          <>
            <p className="text-body-lg font-body-lg text-on-surface mb-1">
              <span className="text-primary font-semibold hover:underline">Click to upload</span> or drag and drop your resume
            </p>
            <p className="text-body-sm font-body-sm text-on-surface-variant max-w-lg mx-auto">
              Supported formats: PDF, DOCX, PNG, JPG (Scanned documents run through automated Tesseract OCR &amp; spaCy pipeline). Maximum payload 25MB.
            </p>
          </>
        )}

        <div className="mt-4 flex items-center justify-center gap-4 text-label-sm font-label-sm text-on-surface-variant flex-wrap">
          <span className="flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px] text-emerald-700">verified_user</span> PII Anonymized
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px] text-primary">bolt</span> ~410ms Latency
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px] text-secondary">dataset</span> Vector Embedding Ready
          </span>
        </div>
      </div>

      {/* Action buttons if file is selected */}
      {selectedFile && (
        <div className="mt-4 flex items-center justify-end gap-3 relative z-10">
          <button
            type="button"
            className="px-4 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container border border-outline-variant text-on-surface text-label-md font-label-md transition-colors"
            onClick={(e) => {
              e.stopPropagation()
              setSelectedFile(null)
              if (fileInputRef.current) fileInputRef.current.value = ''
            }}
            disabled={uploading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="px-5 py-2 rounded-lg bg-primary hover:bg-primary-container text-on-primary text-label-md font-label-md font-semibold transition-all flex items-center gap-2 shadow-sm"
            onClick={(e) => {
              e.stopPropagation()
              handleUpload()
            }}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <span className="btn-spinner"></span>
                <span>Parsing &amp; Extracting Entities...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">psychology</span>
                <span>Extract Entities &amp; Parse</span>
              </>
            )}
          </button>
        </div>
      )}
    </section>
  )
}
