import { useState, useEffect } from 'react'
import { getDashboard } from '../api/subjects'
import './Dashboard.css'

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const result = await getDashboard()
      setData(result)
    } catch (err) {
      setError('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="page-loading">Loading...</div>
  if (error) return <div className="page-loading" style={{ color: 'var(--danger)' }}>{error}</div>

  const subjects = data?.subjects || []

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Dashboard</h1>
        <p className="dashboard-subtitle">Track your progress and weak areas across all subjects</p>
      </div>

      {subjects.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <p className="empty-title">No data yet</p>
          <p className="empty-sub">Take some quizzes to start tracking your progress</p>
        </div>
      ) : (
        <div className="dashboard-grid">
          {subjects.map(subject => {
            const scoreColor = subject.average_score >= 70
              ? 'var(--success)'
              : subject.average_score >= 40
                ? '#B87333'
                : 'var(--danger)'

            return (
              <div key={subject.subject_id} className="dashboard-card">
                <div className="dashboard-card-header">
                  <h2 className="dashboard-card-title">{subject.subject_name}</h2>
                  <div
                    className="dashboard-score"
                    style={{ color: scoreColor, borderColor: scoreColor }}
                  >
                    {subject.average_score}%
                  </div>
                </div>

                <div className="dashboard-stats">
                  <div className="dashboard-stat">
                    <span className="dashboard-stat-value">{subject.total_quizzes}</span>
                    <span className="dashboard-stat-label">Quizzes taken</span>
                  </div>
                  <div className="dashboard-stat">
                    <span
                      className="dashboard-stat-value"
                      style={{ color: scoreColor }}
                    >
                      {subject.average_score}%
                    </span>
                    <span className="dashboard-stat-label">Avg score</span>
                  </div>
                </div>

                {subject.weak_topics.length > 0 ? (
                  <div className="dashboard-weak">
                    <p className="dashboard-weak-title">⚠️ Weak areas</p>
                    <div className="dashboard-weak-list">
                      {subject.weak_topics.map((topic, i) => (
                        <div key={i} className="dashboard-weak-item">
                          <span className="dashboard-weak-name">{topic.topic}</span>
                          <span className="dashboard-weak-count">
                            {topic.wrong_count} wrong
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="dashboard-no-weak">
                    {subject.total_quizzes > 0
                      ? '✅ No weak areas detected yet'
                      : 'Take a quiz to see your weak areas'}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}