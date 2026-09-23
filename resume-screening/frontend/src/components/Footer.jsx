export default function Footer() {
  return (
    <footer className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-4 flex flex-col md:flex-row items-center justify-between gap-4 text-label-md font-label-md text-on-surface-variant warm-card-shadow mt-8">
      <div className="flex flex-wrap items-center gap-4">
        <span className="flex items-center gap-1.5 text-on-surface font-medium">
          <span className="material-symbols-outlined text-[16px] text-primary">terminal</span>
          <span className="font-code-metric">Core Engine: spaCy en_core_web_sm + Tesseract OCR</span>
        </span>
        <span className="text-outline-variant">|</span>
        <span className="flex items-center gap-1 text-on-surface-variant">
          <span className="material-symbols-outlined text-[14px]">speed</span>
          Mean Latency: <span className="text-on-surface font-code-metric font-semibold">~410ms / resume</span>
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span className="px-2.5 py-0.5 rounded bg-surface-container-low border border-outline-variant text-[11px] font-code-metric text-on-surface-variant">
          Model: en_core_web_sm + EntityRuler
        </span>
        <span className="text-label-sm font-label-sm text-outline font-medium">
          ResumeAI Engine Phase 1
        </span>
      </div>
    </footer>
  )
}
