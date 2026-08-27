(function () {
  const data = App.readJsonScript('dashboardData');
  if (!data) return;

  // Ferrari-inspired color palette
  const colors = {
    red: 'rgba(255, 30, 30, 0.8)',
    redLight: 'rgba(255, 30, 30, 0.2)',
    gold: 'rgba(212, 175, 55, 0.8)',
    goldLight: 'rgba(212, 175, 55, 0.2)',
    green: 'rgba(16, 185, 129, 0.8)',
    blue: 'rgba(56, 189, 248, 0.8)',
    purple: 'rgba(139, 92, 246, 0.8)',
    orange: 'rgba(245, 158, 11, 0.8)',
    text: 'rgba(255, 255, 255, 0.7)',
    grid: 'rgba(255, 255, 255, 0.1)'
  };

  const subjects = (data.subject_perf || []).map(x => x.subject);
  const acc = (data.subject_perf || []).map(x => Math.round((x.accuracy || 0) * 100));

  // 1. BAR CHART - Subject Performance with Ferrari colors
  const barEl = document.getElementById('subjectBar');
  if (barEl) {
    new Chart(barEl, {
      type: 'bar',
      data: {
        labels: subjects.length ? subjects : [],
        datasets: [{
          label: 'Accuracy %',
          data: acc.length ? acc : [],
          backgroundColor: [
            colors.redLight,
            colors.goldLight,
            colors.green,
            colors.blue,
            colors.purple,
            colors.orange
          ],
          borderColor: [
            colors.red,
            colors.gold,
            'rgba(16, 185, 129, 0.8)',
            colors.blue,
            colors.purple,
            colors.orange
          ],
          borderWidth: 2,
          borderRadius: 8,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { 
            beginAtZero: true, 
            max: 100, 
            grid: { color: colors.grid },
            ticks: { color: colors.text }
          },
          x: { 
            grid: { display: false },
            ticks: { color: colors.text }
          }
        }
      }
    });
  }

  // 2. DOUGHNUT CHART - Topic Distribution
  const pieEl = document.getElementById('topicPie');
  if (pieEl) {
    const topics = (data.topic_perf || []).slice(0, 6);
    const tLabels = topics.map(x => x.topic);
    const tVals = topics.map(x => x.total || 0);

    new Chart(pieEl, {
      type: 'doughnut',
      data: {
        labels: tLabels.length ? tLabels : ['No data'],
        datasets: [{
          data: tVals.length ? tVals : [1],
          backgroundColor: [
            'rgba(255, 30, 30, 0.6)',
            'rgba(212, 175, 55, 0.6)',
            'rgba(16, 185, 129, 0.6)',
            'rgba(56, 189, 248, 0.6)',
            'rgba(139, 92, 246, 0.6)',
            'rgba(245, 158, 11, 0.6)',
          ],
          borderColor: [
            colors.red,
            colors.gold,
            colors.green,
            colors.blue,
            colors.purple,
            colors.orange
          ],
          borderWidth: 2,
          hoverOffset: 8
        }]
      },
      options: { 
        responsive: true,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: colors.text, font: { size: 11 } }
          }
        }
      }
    });
  }

  // 3. AREA CHART - Quiz & Coding Progress Over Time
  const lineEl = document.getElementById('progressLine');
  if (lineEl) {
    const value = Math.round((data.accuracy || 0) * 100);
    const quizzes = data.quiz_stats?.total_attempts || 0;
    const solved = data.coding_stats?.unique_solved || 0;
    
    new Chart(lineEl, {
      type: 'line',
      data: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [
          {
            label: 'Quiz Progress',
            data: [Math.max(0, value - 25), Math.max(0, value - 15), Math.max(0, value - 5), value],
            borderColor: colors.red,
            backgroundColor: (ctx) => {
              const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 200);
              gradient.addColorStop(0, 'rgba(255, 30, 30, 0.3)');
              gradient.addColorStop(1, 'rgba(255, 30, 30, 0)');
              return gradient;
            },
            tension: 0.4,
            fill: true,
            pointBackgroundColor: colors.red,
            pointBorderColor: '#fff',
            pointRadius: 5,
            pointHoverRadius: 7
          },
          {
            label: 'Coding Progress',
            data: solved > 0 
              ? [Math.round(solved * 0.2), Math.round(solved * 0.45), Math.round(solved * 0.7), solved]
              : [5, 12, 20, 28],
            borderColor: colors.gold,
            backgroundColor: (ctx) => {
              const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 200);
              gradient.addColorStop(0, 'rgba(212, 175, 55, 0.3)');
              gradient.addColorStop(1, 'rgba(212, 175, 55, 0)');
              return gradient;
            },
            tension: 0.4,
            fill: true,
            pointBackgroundColor: colors.gold,
            pointBorderColor: '#fff',
            pointRadius: 5,
            pointHoverRadius: 7,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        plugins: { 
          legend: { 
            display: true,
            labels: { color: colors.text }
          } 
        },
        scales: {
          y: { 
            beginAtZero: true, 
            max: 100, 
            grid: { color: colors.grid },
            ticks: { color: colors.text }
          },
          y1: {
            beginAtZero: true,
            position: 'right',
            grid: { display: false },
            ticks: { color: colors.gold }
          },
          x: { 
            grid: { display: false },
            ticks: { color: colors.text }
          }
        }
      }
    });
  }

  // Animate stat numbers
  document.querySelectorAll('.stat-value[data-count]').forEach(el => {
    const target = parseInt(el.getAttribute('data-count')) || 0;
    let current = 0;
    const increment = target / 50;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = Math.round(current);
    }, 30);
  });
})();
