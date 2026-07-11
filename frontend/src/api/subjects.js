import client from './client'

export const getSubjects = async () => {
  const res = await client.get('/subjects/')
  return res.data
}

export const createSubject = async (name) => {
  const res = await client.post('/subjects/', { name })
  return res.data
}

export const deleteSubject = async (id) => {
  const res = await client.delete(`/subjects/${id}`)
  return res.data
}

export const getSubjectFiles = async (subjectId) => {
  const res = await client.get(`/subjects/${subjectId}/files`)
  return res.data
}

export const getDashboard = async () => {
  const res = await client.get('/subjects/dashboard')
  return res.data
}