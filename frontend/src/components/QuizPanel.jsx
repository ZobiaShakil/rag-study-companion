import { useState } from 'react'
import { generateQuiz, saveQuizSession } from '../api/quiz'
import './QuizPanel.css'

export default function QuizPanel({ collectionName, subjectId, fileId }) {
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [showExplanation, setShowExplanation] = useState(false)
  const [score, setScore] = useState(0)
  const [finished, setFinished] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [numQuestions, setNumQuestions] = useState(5)
  const [results, setResults] = useState([])

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    setQuestions([])
    setCurrentIndex(0)
    setScore(0)
    setFinished(false)
    setResults([])
    setSelectedAnswer(null)

    try {
      const data = await generateQuiz(collectionName, numQuestions)
      setQuestions(data.questions)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate quiz')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswer = (label) => {
    if (selectedAnswer) return
    setSelectedAnswer(label)
    setShowExplanation(true)

    const current = questions[currentIndex]
    const isCorrect = label === current.correct_answer
    if (isCorrect) setScore(prev => prev + 1)

    setResults(prev => [...prev, {
      question: current.question,
      correct_answer: current.correct_answer,
      user_answer: label,
      is_correct: isCorrect,
      topic: current.topic || null
    }])
  }

  const handleNext = async () => {
    if (currentIndex + 1 >= questions.length) {
      setFinished(true)
      try {
        await saveQuizSession(subjectId, fileId, score, questions.length, results)
      } catch (err) {
        console.error('Failed to save quiz session:', err)
      }
    } else {
      setCurrentIndex(prev => prev + 1)
      setSelectedAnswer(null)
      setShowExplanation(false)
    }
  }

  const handleRetry = () => {
    setQuestions([])
    setCurrentIndex(0)
    setScore(0)
    setFinished(false)
    setResults([])
    setSelectedAnswer(null)
    setShowExplanation(false)
  }

  if (finished) {
    const percentage = Math.round((score / questions.length) * 100)
    return (
      <div className="quiz-panel">
        <div className="quiz-finished">
          <div className="quiz-score-circle">
            <span className="quiz-score-num">{percentage}%</span>
            <span className="quiz-score-label">Score</span>
          </div>
          <h2 className="quiz-finished-title">
            {percentage >= 70 ? '🎉 Great job!' : '📖 Keep studying!'}
          </h2>
          <p className="quiz-finished-sub">
            You got {score} out of {questions.length} correct
          </p>
          <div className="quiz-finished-actions">
            <button className="btn-primary" onClick={handleRetry}>
              Try Again
            </button>
            <button className="btn-secondary" onClick={handleGenerate}>
              New Quiz
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (questions.length === 0) {
    return (
      <div className="quiz-panel">
        <div className="quiz-setup">
          <div className="quiz-setup-icon">🧠</div>
          <h2 className="quiz-setup-title">Quiz yourself</h2>
          <p className="quiz-setup-sub">
            Generate MCQs from your uploaded notes
          </p>
          <div className="quiz-setup-options">
            <label className="quiz-setup-label">Number of questions</label>
            <div className="quiz-num-options">
              {[3, 5, 10].map(n => (
                <button
                  key={n}
                  className={`quiz-num-btn ${numQuestions === n ? 'active' : ''}`}
                  onClick={() => setNumQuestions(n)}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          {error && <div className="quiz-error">{error}</div>}
          <button
            className="btn-primary"
            onClick={handleGenerate}
            disabled={loading}
            style={{ marginTop: '16px' }}
          >
            {loading ? 'Generating...' : 'Generate Quiz'}
          </button>
        </div>
      </div>
    )
  }

  const current = questions[currentIndex]
  const progress = ((currentIndex + 1) / questions.length) * 100

  return (
    <div className="quiz-panel">
      <div className="quiz-progress">
        <span className="quiz-progress-text">
          Question {currentIndex + 1} of {questions.length}
        </span>
        <div className="quiz-progress-bar">
          <div
            className="quiz-progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="quiz-score-badge">{score} / {questions.length}</span>
      </div>

      <div className="quiz-card">
        <p className="quiz-question">{current.question}</p>

        <div className="quiz-options">
          {current.options.map(option => {
            let className = 'quiz-option'
            if (selectedAnswer) {
              if (option.label === current.correct_answer) {
                className += ' correct'
              } else if (option.label === selectedAnswer) {
                className += ' wrong'
              }
            }
            return (
              <button
                key={option.label}
                className={className}
                onClick={() => handleAnswer(option.label)}
                disabled={!!selectedAnswer}
              >
                <span className="quiz-option-label">{option.label}</span>
                <span className="quiz-option-text">{option.text}</span>
              </button>
            )
          })}
        </div>

        {showExplanation && (
          <div className={`quiz-explanation ${selectedAnswer === current.correct_answer ? 'correct' : 'wrong'}`}>
            <strong>
              {selectedAnswer === current.correct_answer ? '✓ Correct!' : '✗ Incorrect'}
            </strong>
            <p>{current.explanation}</p>
          </div>
        )}

        {selectedAnswer && (
          <div className="quiz-next">
            <button className="btn-primary" onClick={handleNext}>
              {currentIndex + 1 >= questions.length ? 'See Results' : 'Next →'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}