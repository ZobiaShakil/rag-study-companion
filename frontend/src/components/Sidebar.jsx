import { useState, useRef } from 'react'
import { uploadFile } from '../api/upload'
import './Sidebar.css'

export default function Sidebar({ subjectId, files, activeFile, onFileSelect, onFileUploaded }) {
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    setUploadError(null)

    try {
      const result = await uploadFile(file, subjectId)
      onFileUploaded(result)
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Files</span>
        <button
          className="sidebar-upload-btn"
          onClick={() => fileInputRef.current.click()}
          disabled={uploading}
          title="Upload file"
        >
          {uploading ? '...' : '+'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.pptx"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </div>

      {uploadError && (
        <div className="sidebar-error">{uploadError}</div>
      )}

      {uploading && (
        <div className="sidebar-uploading">
          <div className="sidebar-uploading-bar" />
          <span>Processing file...</span>
        </div>
      )}

      <div className="sidebar-files">
        {files.length === 0 && !uploading ? (
          <div className="sidebar-empty">
            <p>No files yet</p>
            <p>Upload a PDF or PPTX to get started</p>
          </div>
        ) : (
          files.map(file => (
            <button
              key={file.id}
              className={`sidebar-file ${activeFile?.id === file.id ? 'active' : ''}`}
              onClick={() => onFileSelect(file)}
            >
              <span className="sidebar-file-icon">
                {file.filename.endsWith('.pdf') ? '📄' : '📊'}
              </span>
              <span className="sidebar-file-name">{file.filename}</span>
            </button>
          ))
        )}
      </div>
    </aside>
  )
}