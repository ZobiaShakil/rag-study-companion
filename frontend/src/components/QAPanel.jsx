import { useState, useRef, useEffect } from 'react'
import { askQuestion } from '../api/qa'
import CitationCard from './CitationCard'
import './QAPanel.css'

export default function QAPanel({ collectionName, subjectId }) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([]) 
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    const userQuestion = question
    setQuestion('') 
    setError(null)
    setLoading(true)

    setMessages((prev) => [...prev, { role: 'user', text: userQuestion }])

    try {
      // FIX HERE: Pass them as separate positional arguments 
      const data = await askQuestion(userQuestion, collectionName, subjectId)

      setMessages((prev) => [
        ...prev,
        { role: 'model', text: data.answer, sources: data.sources }
      ])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get answer')
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="qa-panel conversational">
      <div className="chat-messages-container">
        {messages.length === 0 && !loading && (
          <div className="qa-empty">
            <p>Ask a question and get answers straight from your notes.</p>
            <p>You can ask follow-up questions to dig deeper into complex topics!</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`chat-bubble-wrapper ${msg.role}`}>
            <div className={`chat-bubble ${msg.role}`}>
              <div className="chat-text">{msg.text}</div>
              
              {msg.sources && msg.sources.length > 0 && (
                <div className="chat-sources-section">
                  <div className="qa-sources-label-sm">Sources Referenced:</div>
                  <div className="citations-list">
                    {msg.sources.map((source, i) => (
                      <CitationCard key={i} source={source} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-bubble-wrapper model">
            <div className="chat-bubble model thinking">
              <span className="dot-flashing">Thinking...</span>
            </div>
          </div>
        )}
        
        <div ref={chatEndRef} />
      </div>

      {error && <div className="qa-error chat-error-banner">{error}</div>}

      <form className="qa-form conversational-input" onSubmit={handleAsk}>
        <input
          className="qa-input"
          type="text"
          placeholder="Ask a question or follow up on a previous point..."
          value={question}
          onChange={e => setQuestion(e.target.value)}
          disabled={loading}
        />
        <button
          className="btn-primary"
          type="submit"
          disabled={!question.trim() || loading}
        >
          Send
        </button>
      </form>
    </div>
  )
}