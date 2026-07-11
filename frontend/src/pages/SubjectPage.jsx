import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getSubjects, getSubjectFiles } from '../api/subjects'
import Sidebar from '../components/Sidebar'
import QAPanel from '../components/QAPanel'
import QuizPanel from '../components/QuizPanel'
import './SubjectPage.css'

export default function SubjectPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const subjectId = parseInt(id)

  const [subject, setSubject] = useState(null)
  const [files, setFiles] = useState([])
  const [activeFile, setActiveFile] = useState(null)
  const [activeTab, setActiveTab] = useState('qa')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      const [subjects, files] = await Promise.all([
        getSubjects(),
        getSubjectFiles(subjectId)
      ])
      const subject = subjects.find(s => s.id === subjectId)
      if (!subject) { navigate('/'); return }
      setSubject(subject)
      setFiles(files)
      if (files.length > 0) setActiveFile(files[0])
    } catch (err) {
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUploaded = (result) => {
    const newFile = {
      id: Date.now(),
      subject_id: subjectId,
      filename: result.filename,
      collection_name: result.collection_name,
      uploaded_at: new Date().toISOString()
    }
    setFiles(prev => [...prev, newFile])
    setActiveFile(newFile)
  }

  if (loading) return <div className="page-loading">Loading...</div>

  return (
    <div className="subject-page">
      <Sidebar
        subjectId={subjectId}
        files={files}
        activeFile={activeFile}
        onFileSelect={setActiveFile}
        onFileUploaded={handleFileUploaded}
      />

      <div className="subject-main">
        <div className="subject-topbar">
          <div className="subject-breadcrumb">
            <button className="breadcrumb-back" onClick={() => navigate('/')}>
              ← Subjects
            </button>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-current">{subject?.name}</span>
            {activeFile && (
              <>
                <span className="breadcrumb-sep">/</span>
                <span className="breadcrumb-file">{activeFile.filename}</span>
              </>
            )}
          </div>

          <div className="subject-tabs">
            <button
              className={`subject-tab ${activeTab === 'qa' ? 'active' : ''}`}
              onClick={() => setActiveTab('qa')}
            >
              💬 Ask
            </button>
            <button
              className={`subject-tab ${activeTab === 'quiz' ? 'active' : ''}`}
              onClick={() => setActiveTab('quiz')}
            >
              🧠 Quiz
            </button>
          </div>
        </div>

        {!activeFile ? (
          <div className="subject-no-file">
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📂</div>
            <p style={{ fontSize: '17px', fontWeight: 500, marginBottom: '8px' }}>
              No file selected
            </p>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              Upload a PDF or PPTX using the + button in the sidebar
            </p>
          </div>
        ) : (
          <>
            {activeTab === 'qa' && (
              <QAPanel collectionName={activeFile.collection_name}
                subjectId={subjectId}
              />
            )}
            {activeTab === 'quiz' && (
              <QuizPanel
                collectionName={activeFile.collection_name}
                subjectId={subjectId}
                fileId={activeFile.id}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}