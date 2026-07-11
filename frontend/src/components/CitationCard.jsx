import './CitationCard.css'

export default function CitationCard({ source }) {
  return (
    <div className="citation-card">
      <div className="citation-meta">
        📄 {source.source} · Slide {source.page}
      </div>
      <p className="citation-text">{source.text}</p>
    </div>
  )
}