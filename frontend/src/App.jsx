import { useState, useRef } from 'react'

const API_URL = 'http://127.0.0.1:8000/analyze'

// Category -> accent color, grounded in the project's own defined waste
// categories rather than a decorative palette. Matches the classification
// logic in Phase 6.
const CATEGORY_STYLE = {
  'Organic/Wet Waste': { color: '#4B5D3A', label: 'Organic / Wet' },
  'Recyclable/Dry Waste': { color: '#A15A28', label: 'Recyclable / Dry' },
  'Glass': { color: '#3E6B6B', label: 'Glass' },
  'Metal': { color: '#546374', label: 'Metal' },
  'E-waste': { color: '#8C3B2E', label: 'E-waste' },
  'Uncertain/Needs Verification': { color: '#8A8370', label: 'Uncertain' },
}

function categoryStyle(category) {
  return CATEGORY_STYLE[category] || { color: '#8A8370', label: category }
}

function ItemCard({ item }) {
  const style = categoryStyle(item.waste_category)
  return (
    <article className="item-card" style={{ '--accent': style.color }}>
      <div className="item-card__head">
        <h3>{item.detected_item}</h3>
        <span className="category-tag">{style.label}</span>
      </div>

      {item.confidence_note && (
        <p className="confidence-note">{item.confidence_note}</p>
      )}

      <dl className="item-card__body">
        <dt>Recommended action</dt>
        <dd>{item.recommended_action}</dd>

        <dt>Why</dt>
        <dd>{item.explanation}</dd>

        {item.sustainability_impact && (
          <>
            <dt>Sustainability impact</dt>
            <dd>{item.sustainability_impact}</dd>
          </>
        )}
      </dl>

      <footer className="item-card__foot">
        {item.grounded_in_sources ? (
          <span className="grounded-badge grounded-badge--yes">Grounded in sources</span>
        ) : (
          <span className="grounded-badge grounded-badge--no">Not fully covered by sources</span>
        )}
        {item.sources && item.sources.length > 0 && (
          <span className="sources">
            {item.sources.map((s) => (
              <span key={s} className="source-pill">{s}</span>
            ))}
          </span>
        )}
      </footer>
    </article>
  )
}

export default function App() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  function handleFileChange(e) {
    const selected = e.target.files?.[0]
    if (!selected) return
    setFile(selected)
    setPreviewUrl(URL.createObjectURL(selected))
    setResult(null)
    setError(null)
  }

  function handleDrop(e) {
    e.preventDefault()
    const dropped = e.dataTransfer.files?.[0]
    if (!dropped) return
    setFile(dropped)
    setPreviewUrl(URL.createObjectURL(dropped))
    setResult(null)
    setError(null)
  }

  async function handleAnalyze() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(API_URL, { method: 'POST', body: formData })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || `Server responded with ${res.status}`)
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(
        err.message?.includes('Failed to fetch')
          ? "Can't reach the backend. Make sure it's running at http://127.0.0.1:8000."
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="masthead">
        <p className="eyebrow">Field guide for waste disposal</p>
        <h1>AI WasteWise</h1>
        <p className="subtitle">AI-powered waste classification and smart disposal assistant</p>
      </header>

      <main>
        <section
          className="upload-zone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          {previewUrl ? (
            <img src={previewUrl} alt="Selected waste item" className="preview-image" />
          ) : (
            <div className="upload-placeholder">
              <p>Drop a photo here, or</p>
              <button
                type="button"
                className="choose-file-btn"
                onClick={() => inputRef.current?.click()}
              >
                Choose an image
              </button>
            </div>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            hidden
          />
          {previewUrl && (
            <button
              type="button"
              className="choose-file-btn choose-file-btn--secondary"
              onClick={() => inputRef.current?.click()}
            >
              Choose a different image
            </button>
          )}
        </section>

        <button
          type="button"
          className="analyze-btn"
          onClick={handleAnalyze}
          disabled={!file || loading}
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>

        {error && <p className="error-banner">{error}</p>}

        {result && result.status === 'uncertain' && (
          <div className="uncertain-panel">
            <h2>Not confident enough to classify</h2>
            <p>{result.uncertainty_reason}</p>
            <p className="uncertain-hint">Try a clearer, closer, well-lit photo of a single item.</p>
          </div>
        )}

        {result && result.status !== 'uncertain' && result.items?.length > 0 && (
          <section className="results">
            {result.status === 'multi_item' && (
              <p className="multi-item-note">
                {result.items.length} items detected — each classified separately.
              </p>
            )}
            {result.items.map((item, i) => (
              <ItemCard item={item} key={i} />
            ))}
          </section>
        )}
      </main>

      <footer className="page-footer">
        <p>AI-assisted classification — recommendations are grounded in the sources shown above, not guaranteed accurate for every case.</p>
      </footer>
    </div>
  )
}
