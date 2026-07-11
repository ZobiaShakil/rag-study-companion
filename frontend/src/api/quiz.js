import client from './client'

export const generateQuiz = async (collectionName, numQuestions = 5, topic = null) => {
  const res = await client.post('/quiz/generate', {
    collection_name: collectionName,
    num_questions: numQuestions,
    topic
  })
  return res.data
}

export const saveQuizSession = async (subjectId, fileId, score, total, results) => {
  const res = await client.post('/quiz/sessions', {
    subject_id: subjectId,
    file_id: fileId,
    score,
    total,
    results
  })
  return res.data
}