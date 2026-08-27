(function () {
  const host = document.getElementById('quizHost');
  if (!host) return;

  const quiz = App.readJsonScript('quizData');
  const questions = (quiz && quiz.questions) ? quiz.questions : [];

  let index = 0;
  const answers = {};

  function render() {
    host.innerHTML = '';

    if (!questions.length) {
      const empty = document.createElement('div');
      empty.className = 'muted';
      empty.textContent = 'No quiz questions found in dataset yet. Add intents.json entries.';
      host.appendChild(empty);
      return;
    }

    const q = questions[index];

    const card = document.createElement('div');
    card.className = 'q';

    const title = document.createElement('div');
    title.className = 'q-title';
    title.textContent = `Q${index + 1}/${questions.length}: ${q.question}`;
    card.appendChild(title);

    const opts = document.createElement('div');
    opts.className = 'options';

    (q.options || []).forEach((opt) => {
      const btn = document.createElement('div');
      btn.className = 'opt' + ((answers[String(q.id)] === opt) ? ' selected' : '');
      btn.textContent = opt;
      btn.addEventListener('click', () => {
        answers[String(q.id)] = opt;
        render();
      });
      opts.appendChild(btn);
    });

    card.appendChild(opts);

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '10px';
    actions.style.marginTop = '12px';

    const prev = document.createElement('button');
    prev.className = 'btn-secondary';
    prev.textContent = 'Prev';
    prev.disabled = index === 0;
    prev.addEventListener('click', () => { index = Math.max(0, index - 1); render(); });

    const next = document.createElement('button');
    next.className = 'btn-secondary';
    next.textContent = 'Next';
    next.disabled = index === questions.length - 1;
    next.addEventListener('click', () => { index = Math.min(questions.length - 1, index + 1); render(); });

    const submit = document.createElement('button');
    submit.className = 'btn-primary';
    submit.textContent = 'Submit';
    submit.addEventListener('click', onSubmit);

    actions.appendChild(prev);
    actions.appendChild(next);
    actions.appendChild(submit);

    host.appendChild(card);
    host.appendChild(actions);
  }

  async function onSubmit() {
    const resp = await fetch('/api/quiz/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quiz, answers })
    });

    const data = await resp.json();
    showResults(data);
  }

  async function showResults(data) {
    host.innerHTML = '';
    
    const percentage = (data.accuracy * 100).toFixed(0);
    const isExcellent = data.accuracy >= 0.8;
    const isGood = data.accuracy >= 0.6;
    
    // Create results container
    const container = document.createElement('div');
    container.className = 'quiz-results';
    
    // Score Summary Section
    const summarySection = document.createElement('div');
    summarySection.className = 'glass-card result-summary';
    summarySection.innerHTML = `
      <div class="score-header">
        <div class="score-badge ${isExcellent ? 'excellent' : isGood ? 'good' : 'needs-improvement'}">
          ${percentage}%
        </div>
        <div class="score-text">
          <div class="score-main">${data.score} / ${data.total}</div>
          <div class="score-sub">Correct Answers</div>
        </div>
      </div>
      <div class="score-message">
        ${getPerformanceMessage(data.accuracy)}
      </div>
    `;
    container.appendChild(summarySection);
    
    // Question Review Section
    const reviewSection = document.createElement('div');
    reviewSection.className = 'glass-card question-review';
    reviewSection.innerHTML = `
      <div class="review-header">
        <div class="card-label">Question Review</div>
        <div class="review-stats">
          <span class="stat correct">${data.results.filter(r => r.is_correct).length} Correct</span>
          <span class="stat incorrect">${data.results.filter(r => !r.is_correct).length} Incorrect</span>
        </div>
      </div>
      <div class="questions-list">
        ${data.results.map((r, i) => `
          <div class="question-item ${r.is_correct ? 'correct' : 'incorrect'}">
            <div class="q-number">${i + 1}</div>
            <div class="q-content">
              <div class="q-text">${r.question}</div>
              <div class="q-answers">
                <span class="your-answer ${r.is_correct ? 'correct' : 'wrong'}">
                  Your: ${r.your_answer || 'Not answered'}
                </span>
                ${!r.is_correct ? `<span class="correct-answer">Correct: ${r.correct_answer}</span>` : ''}
              </div>
              <div class="q-topic">
                <span class="topic-tag">${r.topic}</span>
              </div>
            </div>
            <div class="q-status">
              ${r.is_correct ? '✓' : '✗'}
            </div>
          </div>
        `).join('')}
      </div>
    `;
    container.appendChild(reviewSection);
    
    // AI Suggestions Section (with loading state)
    const suggestionsSection = document.createElement('div');
    suggestionsSection.className = 'glass-card ai-suggestions';
    suggestionsSection.innerHTML = `
      <div class="suggestions-header">
        <div class="card-label">
          <span class="ai-icon">🤖</span> AI-Powered Suggestions
        </div>
      </div>
      <div class="suggestions-content" id="suggestionsContent">
        <div class="loading-spinner">
          <div class="spinner"></div>
          <div class="loading-text">Generating personalized suggestions...</div>
        </div>
      </div>
    `;
    container.appendChild(suggestionsSection);
    
    // Action Buttons
    const actionsSection = document.createElement('div');
    actionsSection.className = 'result-actions';
    actionsSection.innerHTML = `
      <a href="${window.location.pathname + window.location.search}" class="btn-secondary">Retake Quiz</a>
      <a href="/student/dashboard" class="btn-primary">Back to Dashboard</a>
    `;
    container.appendChild(actionsSection);
    
    host.appendChild(container);
    
    // Load AI suggestions
    loadSuggestions(data);
  }

  async function loadSuggestions(data) {
    try {
      const resp = await fetch('/api/quiz/suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score: data.score,
          total: data.total,
          accuracy: data.accuracy,
          weak_topics: data.weak_topics,
          config: data.config
        })
      });
      
      const suggestionData = await resp.json();
      const contentDiv = document.getElementById('suggestionsContent');
      
      if (suggestionData.suggestions) {
        // Format suggestions with markdown-style bullets
        const formatted = suggestionData.suggestions
          .replace(/•/g, '<span class="bullet">•</span>')
          .replace(/Summary:/g, '<div class="suggestion-summary-title">Summary:</div>')
          .replace(/Suggestions:/g, '<div class="suggestion-list-title">Suggestions:</div>')
          .replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = `<div class="suggestion-text">${formatted}</div>`;
      } else {
        contentDiv.innerHTML = `
          <div class="suggestion-fallback">
            <p>Great effort! To improve your performance:</p>
            <ul>
              <li>Review the topics you got wrong: ${data.weak_topics.join(', ') || 'Practice more'}</li>
              <li>Try similar quizzes to reinforce your knowledge</li>
              <li>Use Chat AI to ask questions about challenging concepts</li>
            </ul>
          </div>
        `;
      }
    } catch (e) {
      document.getElementById('suggestionsContent').innerHTML = `
        <div class="suggestion-error">
          <p>Keep practicing! Focus on: ${data.weak_topics.join(', ') || 'all topics'}</p>
        </div>
      `;
    }
  }

  function getPerformanceMessage(accuracy) {
    if (accuracy >= 0.8) return "🎉 Outstanding! You're mastering this topic!";
    if (accuracy >= 0.6) return "👍 Good job! Keep practicing to improve further.";
    if (accuracy >= 0.4) return "💪 You're making progress! Review the incorrect answers.";
    return "📚 Keep learning! Focus on understanding the fundamentals.";
  }

  render();
})();

// Add styles
document.head.insertAdjacentHTML('beforeend', `
<style>
.quiz-results {
  display: grid;
  gap: 20px;
}
.result-summary {
  padding: 28px;
  text-align: center;
}
.score-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 16px;
}
.score-badge {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
  color: white;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.score-badge.excellent { background: linear-gradient(135deg, #10b981, #059669); }
.score-badge.good { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.score-badge.needs-improvement { background: linear-gradient(135deg, #f59e0b, #d97706); }
.score-main {
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
}
.score-sub {
  font-size: 16px;
  color: rgba(226, 232, 240, 0.7);
  margin-top: 4px;
}
.score-message {
  font-size: 18px;
  color: rgba(226, 232, 240, 0.9);
  padding: 12px 20px;
  background: rgba(148, 163, 184, 0.1);
  border-radius: 12px;
  display: inline-block;
}
.question-review {
  padding: 24px;
}
.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.review-stats {
  display: flex;
  gap: 12px;
}
.stat {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}
.stat.correct { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.stat.incorrect { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.questions-list {
  display: grid;
  gap: 12px;
}
.question-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  background: rgba(15, 23, 42, 0.4);
  align-items: flex-start;
}
.question-item.correct { border-left: 4px solid #10b981; }
.question-item.incorrect { border-left: 4px solid #ef4444; }
.q-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(148, 163, 184, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}
.q-content { flex: 1; }
.q-text {
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.4;
}
.q-answers {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}
.your-answer {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
}
.your-answer.correct { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.your-answer.wrong { background: rgba(239, 68, 68, 0.2); color: #f87171; text-decoration: line-through; }
.correct-answer {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}
.q-topic { margin-top: 8px; }
.topic-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}
.q-status {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}
.question-item.correct .q-status { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.question-item.incorrect .q-status { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.ai-suggestions {
  padding: 24px;
}
.suggestions-header {
  margin-bottom: 16px;
}
.ai-icon {
  margin-right: 6px;
}
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  gap: 16px;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(148, 163, 184, 0.2);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.loading-text {
  color: rgba(226, 232, 240, 0.7);
  font-size: 14px;
}
.suggestion-text {
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.9);
}
.suggestion-summary-title {
  font-weight: 700;
  color: #38bdf8;
  margin-bottom: 8px;
  font-size: 16px;
}
.suggestion-list-title {
  font-weight: 700;
  color: #34d399;
  margin: 16px 0 8px;
  font-size: 16px;
}
.bullet {
  color: #34d399;
  margin-right: 8px;
}
.suggestion-fallback, .suggestion-error {
  padding: 16px;
  background: rgba(148, 163, 184, 0.1);
  border-radius: 12px;
}
.suggestion-fallback ul {
  margin: 12px 0 0 20px;
  padding: 0;
}
.suggestion-fallback li {
  margin-bottom: 8px;
  color: rgba(226, 232, 240, 0.8);
}
.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 8px;
}
@media (max-width: 600px) {
  .score-header { flex-direction: column; }
  .score-main { font-size: 32px; }
  .review-header { flex-direction: column; align-items: flex-start; }
  .q-answers { flex-direction: column; }
  .result-actions { flex-direction: column; }
}
</style>
`);
