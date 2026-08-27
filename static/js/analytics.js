(function () {
  const data = App.readJsonScript('analyticsData');
  if (!data) return;

  // Ferrari-inspired color palette
  const colors = {
    red: 'rgba(255, 30, 30, 0.8)',
    redLight: 'rgba(255, 30, 30, 0.2)',
    gold: 'rgba(212, 175, 55, 0.8)',
    goldLight: 'rgba(212, 175, 55, 0.2)',
    green: 'rgba(16, 185, 129, 0.8)',
    greenLight: 'rgba(16, 185, 129, 0.2)',
    blue: 'rgba(56, 189, 248, 0.8)',
    blueLight: 'rgba(56, 189, 248, 0.2)',
    purple: 'rgba(139, 92, 246, 0.8)',
    purpleLight: 'rgba(139, 92, 246, 0.2)',
    orange: 'rgba(245, 158, 11, 0.8)',
    orangeLight: 'rgba(245, 158, 11, 0.2)',
    grid: 'rgba(255, 255, 255, 0.1)',
    text: 'rgba(255, 255, 255, 0.7)'
  };

  const chartColors = [
    colors.red, colors.gold, colors.green, colors.blue, colors.purple, colors.orange
  ];

  const chartColorsLight = [
    colors.redLight, colors.goldLight, colors.greenLight, colors.blueLight, colors.purpleLight, colors.orangeLight
  ];

  // Common chart options
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: { color: colors.text, font: { size: 12 } }
      }
    },
    scales: {
      x: {
        grid: { color: colors.grid },
        ticks: { color: colors.text }
      },
      y: {
        grid: { color: colors.grid },
        ticks: { color: colors.text }
      }
    }
  };

  // 1. RADAR CHART - Subject Performance Overview
  const radarEl = document.getElementById('radarChart');
  if (radarEl && data.subject_perf) {
    const subjects = data.subject_perf.map(s => s.subject);
    const accuracies = data.subject_perf.map(s => Math.round((s.accuracy || 0) * 100));
    
    new Chart(radarEl, {
      type: 'radar',
      data: {
        labels: subjects,
        datasets: [{
          label: 'Accuracy %',
          data: accuracies,
          backgroundColor: colors.redLight,
          borderColor: colors.red,
          borderWidth: 2,
          pointBackgroundColor: colors.red,
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: colors.red
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          r: {
            angleLines: { color: colors.grid },
            grid: { color: colors.grid },
            pointLabels: { color: colors.text, font: { size: 11 } },
            ticks: { color: colors.text, backdropColor: 'transparent' },
            suggestedMin: 0,
            suggestedMax: 100
          }
        }
      }
    });
  }

  // 2. DOUGHNUT CHART - Questions Distribution
  const doughnutEl = document.getElementById('doughnutChart');
  if (doughnutEl && data.topic_perf) {
    const topics = data.topic_perf.slice(0, 5);
    const labels = topics.map(t => t.topic);
    const values = topics.map(t => t.total);
    
    new Chart(doughnutEl, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: chartColorsLight.map(c => c.replace('0.2', '0.6')),
          borderColor: chartColors,
          borderWidth: 2,
          hoverOffset: 10
        }]
      },
      options: {
        responsive: true,
        cutout: '60%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: colors.text, font: { size: 11 }, padding: 15 }
          }
        }
      }
    });
  }

  // 3. POLAR AREA CHART - Performance by Band
  const polarEl = document.getElementById('polarChart');
  if (polarEl && data.topic_perf) {
    const bands = { strong: 0, medium: 0, weak: 0 };
    data.topic_perf.forEach(t => {
      if (t.band && bands[t.band] !== undefined) bands[t.band]++;
    });
    
    new Chart(polarEl, {
      type: 'polarArea',
      data: {
        labels: ['Strong', 'Medium', 'Weak'],
        datasets: [{
          data: [bands.strong, bands.medium, bands.weak],
          backgroundColor: [
            'rgba(16, 185, 129, 0.6)',
            'rgba(245, 158, 11, 0.6)',
            'rgba(239, 68, 68, 0.6)'
          ],
          borderColor: [
            colors.green,
            colors.orange,
            colors.red
          ],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { color: colors.text } } },
        scales: {
          r: {
            grid: { color: colors.grid },
            ticks: { color: colors.text, backdropColor: 'transparent' }
          }
        }
      }
    });
  }

  // 4. LINE CHART - Quiz Trend Over Time
  const quizTrendEl = document.getElementById('quizTrendChart');
  if (quizTrendEl) {
    // Generate mock time-based data if not available
    const quizzes = data.quiz_stats?.total_attempts || 0;
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const trendData = quizzes > 0 
      ? months.map((_, i) => Math.max(0, Math.round(quizzes * (i + 1) / 6 - Math.random() * 2)))
      : months.map(() => Math.floor(Math.random() * 5));
    
    new Chart(quizTrendEl, {
      type: 'line',
      data: {
        labels: months,
        datasets: [{
          label: 'Quizzes Attended',
          data: trendData,
          borderColor: colors.red,
          backgroundColor: colors.redLight,
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: colors.red,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7
        }]
      },
      options: {
        ...commonOptions,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text } },
          y: { beginAtZero: true, grid: { color: colors.grid }, ticks: { color: colors.text } }
        }
      }
    });
  }

  // 5. AREA CHART - Questions Solved Progress
  const questionsEl = document.getElementById('questionsChart');
  if (questionsEl) {
    const solved = data.coding_stats?.unique_solved || 0;
    const weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
    const progressData = solved > 0
      ? weeks.map((_, i) => Math.round(solved * (i + 1) / 4))
      : [5, 12, 20, 28];
    
    new Chart(questionsEl, {
      type: 'line',
      data: {
        labels: weeks,
        datasets: [{
          label: 'Questions Solved',
          data: progressData,
          borderColor: colors.gold,
          backgroundColor: (ctx) => {
            const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, 'rgba(212, 175, 55, 0.4)');
            gradient.addColorStop(1, 'rgba(212, 175, 55, 0)');
            return gradient;
          },
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: colors.gold,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8
        }]
      },
      options: {
        ...commonOptions,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text } },
          y: { beginAtZero: true, grid: { color: colors.grid }, ticks: { color: colors.text } }
        }
      }
    });
  }

  // 6. STACKED BAR CHART - Correct vs Incorrect
  const stackedEl = document.getElementById('stackedChart');
  if (stackedEl && data.subject_perf) {
    const subjects = data.subject_perf.map(s => s.subject);
    const correct = data.subject_perf.map(s => s.correct || 0);
    const incorrect = data.subject_perf.map(s => s.incorrect || 0);
    
    new Chart(stackedEl, {
      type: 'bar',
      data: {
        labels: subjects,
        datasets: [
          {
            label: 'Correct',
            data: correct,
            backgroundColor: colors.green,
            borderRadius: 4
          },
          {
            label: 'Incorrect',
            data: incorrect,
            backgroundColor: colors.red,
            borderRadius: 4
          }
        ]
      },
      options: {
        ...commonOptions,
        plugins: {
          legend: {
            position: 'top',
            labels: { color: colors.text, usePointStyle: true, padding: 20 }
          }
        },
        scales: {
          x: { stacked: true, grid: { display: false }, ticks: { color: colors.text } },
          y: { stacked: true, beginAtZero: true, grid: { color: colors.grid }, ticks: { color: colors.text } }
        }
      }
    });
  }

  // 7. BUBBLE CHART - Difficulty vs Accuracy
  const bubbleEl = document.getElementById('bubbleChart');
  if (bubbleEl && data.topic_perf) {
    const bubbleData = data.topic_perf.slice(0, 8).map((t, i) => ({
      x: t.total || Math.random() * 50 + 10, // Number of questions as difficulty proxy
      y: Math.round((t.accuracy || 0) * 100),
      r: Math.max(5, (t.correct || 0) / 2) // Bubble size based on correct answers
    }));
    
    new Chart(bubbleEl, {
      type: 'bubble',
      data: {
        datasets: [{
          label: 'Topics',
          data: bubbleData,
          backgroundColor: chartColorsLight.map(c => c.replace('0.2', '0.5')),
          borderColor: chartColors,
          borderWidth: 2
        }]
      },
      options: {
        ...commonOptions,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Questions: ${ctx.raw.x}, Accuracy: ${ctx.raw.y}%`
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'Questions Attempted', color: colors.text },
            grid: { color: colors.grid },
            ticks: { color: colors.text }
          },
          y: {
            title: { display: true, text: 'Accuracy %', color: colors.text },
            beginAtZero: true,
            max: 100,
            grid: { color: colors.grid },
            ticks: { color: colors.text }
          }
        }
      }
    });
  }

  // Animate bar fills
  document.querySelectorAll('.bar-fill[data-width]').forEach((el) => {
    const w = Math.max(0, Math.min(100, parseInt(el.getAttribute('data-width') || '0', 10)));
    requestAnimationFrame(() => { el.style.width = w + '%'; });
  });
})();
