import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSubjects, createSubject, deleteSubject } from '../api/subjects'
import CreateSubjectModal from '../components/CreateSubjectModal'
import './HomePage.css'

export default function HomePage() {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadSubjects()
  }, [])

  const loadSubjects = async () => {
    try {
      const data = await getSubjects()
      setSubjects(data)
    } catch (err) {
      setError('Failed to load subjects. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (name) => {
    try {
      const subject = await createSubject(name)
      setSubjects(prev => [...prev, subject])
      setShowModal(false)
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create subject')
    }
  }

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this subject and all its files?')) return
    try {
      await deleteSubject(id)
      setSubjects(prev => prev.filter(s => s.id !== id))
    } catch (err) {
      alert('Failed to delete subject')
    }
  }

  if (loading) return <div className="page-loading">Loading...</div>

  return (
    <div className="home-page">
      <div className="home-header">
        <div>
          <h1 className="home-title">My Subjects</h1>
          <p className="home-subtitle">Pick a subject to study or create a new one</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          + New Subject
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {subjects.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <p className="empty-title">No subjects yet</p>
          <p className="empty-sub">Create your first subject to get started</p>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            + Create Subject
          </button>
        </div>
      ) : (
        <div className="subjects-grid">
          {subjects.map(subject => (
            <div
              key={subject.id}
              className="subject-card"
              onClick={() => navigate(`/subject/${subject.id}`)}
            >
              <div className="subject-card-icon">📁</div>
              <div className="subject-card-body">
                <h3 className="subject-card-name">{subject.name}</h3>
                <p className="subject-card-meta">
                  {subject.file_count} {subject.file_count === 1 ? 'file' : 'files'}
                </p>
              </div>
              <button
                className="subject-card-delete"
                onClick={(e) => handleDelete(e, subject.id)}
                title="Delete subject"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <CreateSubjectModal
          onClose={() => setShowModal(false)}
          onCreate={handleCreate}
        />
      )}
    </div>
  )
}