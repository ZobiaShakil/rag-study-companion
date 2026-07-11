import client from './client'

export const uploadFile = async (file, subjectId) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('subject_id', subjectId)

  const res = await client.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}