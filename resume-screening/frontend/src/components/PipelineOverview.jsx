export default function PipelineOverview() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 relative overflow-hidden warm-card-shadow">
        <div className="absolute top-0 right-0 w-96 h-48 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
        <h2 className="text-headline-md font-headline-md text-on-surface flex items-center gap-2">
          System Architecture &amp; Processing Pipeline
          <span className="material-symbols-outlined text-primary text-[24px]">hub</span>
        </h2>
        <p className="text-body-md font-body-md text-on-surface-variant mt-1">
          Phase 1: Multi-Format Ingestion, Hybrid Parsing (Native + OCR), and NER Skills Taxonomy Extraction.
        </p>
      </div>

      {/* Pipeline Flow Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Step 1 */}
        <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 relative flex flex-col justify-between warm-card-shadow">
          <span className="absolute top-4 right-4 text-headline-sm font-code-metric font-bold text-outline-variant">
            01
          </span>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-primary-fixed border border-primary/25 text-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px]">upload_file</span>
            </div>
            <h3 className="text-title-lg font-title-lg text-on-surface font-bold">Multi-Format Ingestion</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant">
              Accepts PDF, Microsoft Word DOCX, and scanned image formats (PNG, JPG, TIFF) via asynchronous file streaming.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-outline-variant/50">
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-on-surface">PDF</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-on-surface">DOCX</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-on-surface">Scanned</span>
          </div>
        </div>

        {/* Step 2 */}
        <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 relative flex flex-col justify-between warm-card-shadow">
          <span className="absolute top-4 right-4 text-headline-sm font-code-metric font-bold text-outline-variant">
            02
          </span>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-secondary-fixed border border-secondary/30 text-secondary flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px]">document_scanner</span>
            </div>
            <h3 className="text-title-lg font-title-lg text-on-surface font-bold">Hybrid Parsing &amp; OCR</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant">
              Decodes native text layout using pdfplumber &amp; python-docx. Falls back automatically to Tesseract OCR when text density is &lt; 50 chars.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-outline-variant/50">
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-secondary">pdfplumber</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-secondary">python-docx</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-secondary">pytesseract</span>
          </div>
        </div>

        {/* Step 3 */}
        <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 relative flex flex-col justify-between warm-card-shadow">
          <span className="absolute top-4 right-4 text-headline-sm font-code-metric font-bold text-outline-variant">
            03
          </span>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-primary-fixed border border-primary/25 text-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px]">psychology</span>
            </div>
            <h3 className="text-title-lg font-title-lg text-on-surface font-bold">NLP &amp; Named Entities</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant">
              spaCy en_core_web_sm pipeline extracts names, organizations, and degrees. Regex isolates verified emails, phones, and profile URLs.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-outline-variant/50">
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-primary">spaCy NER</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-primary">EntityRuler</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-primary">Regex</span>
          </div>
        </div>

        {/* Step 4 */}
        <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 relative flex flex-col justify-between warm-card-shadow">
          <span className="absolute top-4 right-4 text-headline-sm font-code-metric font-bold text-outline-variant">
            04
          </span>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-surface-container-low border border-outline-variant text-tertiary flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px]">category</span>
            </div>
            <h3 className="text-title-lg font-title-lg text-on-surface font-bold">Skills Taxonomy (6 Domains)</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant">
              PhraseMatcher indexes 1000+ technical skills categorized into languages, frameworks, databases, devops, tools, and methodologies.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-outline-variant/50">
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-tertiary">PhraseMatcher</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-tertiary">1000+ Skills</span>
          </div>
        </div>

        {/* Step 5 */}
        <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 relative flex flex-col justify-between warm-card-shadow">
          <span className="absolute top-4 right-4 text-headline-sm font-code-metric font-bold text-outline-variant">
            05
          </span>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-800 flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px]">database</span>
            </div>
            <h3 className="text-title-lg font-title-lg text-on-surface font-bold">Async Persistence</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant">
              Stores validated Pydantic v2 schemas in MongoDB using the asynchronous Motor driver for non-blocking I/O.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-outline-variant/50">
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-emerald-800">MongoDB</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-emerald-800">Motor</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-low border border-outline-variant text-emerald-800">Pydantic v2</span>
          </div>
        </div>

        {/* Step 6 */}
        <div className="rounded-xl bg-surface-container-low border border-dashed border-primary/40 p-6 relative flex flex-col justify-between warm-card-shadow">
          <span className="absolute top-4 right-4 text-label-sm font-label-sm px-2 py-0.5 rounded bg-primary-fixed text-primary font-bold">
            Phase 2/3
          </span>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-surface-container-lowest border border-outline-variant text-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px]">model_training</span>
            </div>
            <h3 className="text-title-lg font-title-lg text-on-surface font-bold">Semantic Embeddings &amp; Ranking</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant">
              Modular architecture ready for Sentence-BERT dense vector embeddings, cosine similarity ranking, and demographic parity bias audits.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-outline-variant/50">
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-lowest text-primary">Sentence-BERT</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-lowest text-secondary">Cosine Sim</span>
            <span className="px-2 py-0.5 rounded text-label-sm font-label-sm bg-surface-container-lowest text-tertiary">Fairness Audit</span>
          </div>
        </div>
      </div>

      {/* Specifications Table */}
      <div className="rounded-xl bg-surface-container-lowest border border-outline-variant/80 p-6 warm-card-shadow space-y-4">
        <h3 className="text-title-lg font-title-lg text-on-surface font-bold flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[20px]">tune</span>
          Engineering Specifications
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-body-sm font-body-sm">
            <thead className="border-b border-outline-variant/70 text-label-sm font-label-sm text-outline uppercase">
              <tr>
                <th className="py-2.5 px-3">Subsystem</th>
                <th className="py-2.5 px-3">Engine &amp; Driver</th>
                <th className="py-2.5 px-3">Specification</th>
                <th className="py-2.5 px-3">Phase 1 Operational Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/40">
              <tr>
                <td className="py-2.5 px-3 font-semibold text-on-surface">API Backend</td>
                <td className="py-2.5 px-3">FastAPI + Uvicorn</td>
                <td className="py-2.5 px-3 font-code-metric">Python 3.11</td>
                <td className="py-2.5 px-3 text-on-surface-variant">REST routing, async lifespan, file streaming</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-on-surface">Document Parsing</td>
                <td className="py-2.5 px-3">pdfplumber &amp; python-docx</td>
                <td className="py-2.5 px-3 font-code-metric">v0.11+ / v1.1+</td>
                <td className="py-2.5 px-3 text-on-surface-variant">Digital layout &amp; character stream extraction</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-on-surface">OCR Engine</td>
                <td className="py-2.5 px-3">pytesseract + pdf2image</td>
                <td className="py-2.5 px-3 font-code-metric">Tesseract 5.3</td>
                <td className="py-2.5 px-3 text-on-surface-variant">Low-density &amp; scanned bitmap text recovery</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-on-surface">NER &amp; Taxonomy</td>
                <td className="py-2.5 px-3">spaCy + PhraseMatcher</td>
                <td className="py-2.5 px-3 font-code-metric">en_core_web_sm</td>
                <td className="py-2.5 px-3 text-on-surface-variant">Entity extraction + 6-domain skills catalog</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold text-on-surface">Persistence</td>
                <td className="py-2.5 px-3">MongoDB + Motor</td>
                <td className="py-2.5 px-3 font-code-metric">Pydantic v2</td>
                <td className="py-2.5 px-3 text-on-surface-variant">Non-blocking NoSQL document storage</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
