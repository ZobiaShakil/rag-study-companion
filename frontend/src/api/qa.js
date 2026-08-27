import client from './client'

export const askQuestion = async (question, collectionName, subjectId, topK = 3) => {
  const res = await client.post('/qa/ask', {
    question,
    collection_name: collectionName,
    subject_id: subjectId,
    top_k: topK
  })
  return res.data
}

export const getHistory = async (subjectId) => {
  const res = await client.get(`/qa/history/${subjectId}`)
  return res.data
}