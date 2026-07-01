document.addEventListener('DOMContentLoaded', () => {
  const genreList = document.getElementById('genre-list')
  const directorList = document.getElementById('director-list')
  const reviewerList = document.getElementById('reviewer-list')
  const yearList = document.getElementById('year-list')
  const avgRuntime = document.getElementById('avg-runtime')
  const tbody = document.querySelector('#stats-table tbody')
  const thead = document.querySelector('#stats-table thead')

  const reviewerFilter = document.createElement('select')
  reviewerFilter.id = 'reviewer-filter'
  reviewerFilter.innerHTML = '<option value="">Alle anmeldere</option>'
  document.querySelector('.stats-panel').prepend(reviewerFilter)

  // Create visualization section
  const vizSection = document.createElement('section')
  vizSection.className = 'visualizations'
  vizSection.innerHTML = `
    <h2>Visualiseringer</h2>
    <div class="viz-grid">
      <div class="viz-container">
        <h3>Fordelingen af vurderinger (1-10)</h3>
        <canvas id="rating-dist-chart"></canvas>
      </div>
      <div class="viz-container">
        <h3>Vurderinger pr. år</h3>
        <canvas id="ratings-per-year-chart"></canvas>
      </div>
      <div class="viz-container">
        <h3>Gennemsnitlige vurderinger pr. år</h3>
        <canvas id="avg-rating-per-year-chart"></canvas>
      </div>
    </div>
  `
  document.querySelector('.right').appendChild(vizSection)

  let charts = {}
  let reviewers = []

  async function loadReviewers() {
    try {
      const res = await fetch('/api/reviewers')
      reviewers = await res.json()
      reviewers.forEach(r => {
        const opt = document.createElement('option')
        opt.value = r
        opt.textContent = r
        reviewerFilter.appendChild(opt)
      })
    } catch (err) {
      console.error('Could not load reviewers', err)
    }
  }

  function buildHeader() {
    const headers = ['Titel','Gns.','Antal','Instruktør','År','Runtime']
    thead.innerHTML = '<tr>' + headers.map(h => `<th>${escapeHtml(h)}</th>`).join('') + '</tr>'
  }

  async function renderAll(selectedReviewer) {
    try {
      const statsRes = await fetch('/api/stats' + (selectedReviewer ? `?reviewer=${encodeURIComponent(selectedReviewer)}` : ''))
      const stats = await statsRes.json()
      const reviewsRes = await fetch('/api/reviews' + (selectedReviewer ? `?reviewer=${encodeURIComponent(selectedReviewer)}` : ''))
      const reviews = await reviewsRes.json()

      const movies = stats.movies || []
      const aggregates = stats.aggregates || {}

      // KPIs
      genreList.innerHTML = (aggregates.top_genres || []).map(([g,c]) => `<li>${escapeHtml(g)} (${c})</li>`).join('') || '<li>Ingen data</li>'
      directorList.innerHTML = (aggregates.top_directors || []).map(([d,c]) => `<li>${escapeHtml(d)} (${c})</li>`).join('') || '<li>Ingen data</li>'
      reviewerList.innerHTML = (aggregates.top_reviewers || []).map(([r,c]) => `<li>${escapeHtml(r)} (${c})</li>`).join('') || '<li>Ingen data</li>'
      yearList.innerHTML = (aggregates.years || []).map(([y,c]) => `<li>${escapeHtml(y)} (${c})</li>`).join('') || '<li>Ingen data</li>'
      avgRuntime.textContent = aggregates.avg_runtime ? `${aggregates.avg_runtime} min` : 'Ingen data'

      // Simple table: one row per movie
      tbody.innerHTML = movies.map(movie => {
        return `
          <tr>
            <td>${escapeHtml(movie.title)}</td>
            <td>${movie.avg_rating}</td>
            <td>${movie.count}</td>
            <td>${escapeHtml(movie.director || '-')}</td>
            <td>${movie.release_year || '-'}</td>
            <td>${movie.runtime ? movie.runtime + ' min' : '-'}</td>
          </tr>
        `
      }).join('')

      // Render charts
      renderCharts(reviews, aggregates)
    } catch (err) {
      console.error(err)
    }
  }

  function renderCharts(reviews, aggregates) {
    // Rating distribution (1-10)
    const dist = Array.from({length:10}, () => 0)
    const yearCounts = {}
    const yearAvgRatings = {}
    
    reviews.forEach(r => {
      const v = parseInt(r.rating)
      if (v >= 1 && v <= 10) dist[v-1]++
      
      const year = r.release_year || 'Ukendt'
      yearCounts[year] = (yearCounts[year] || 0) + 1
      yearAvgRatings[year] = (yearAvgRatings[year] || 0) + v
    })

    // Calculate year averages
    Object.keys(yearAvgRatings).forEach(year => {
      yearAvgRatings[year] = (yearAvgRatings[year] / yearCounts[year]).toFixed(1)
    })

    renderDistributionChart(dist)
    renderYearCountsChart(yearCounts, aggregates.years || [])
    renderYearAvgChart(yearAvgRatings, aggregates.years || [])
  }

  function renderDistributionChart(dist) {
    const ctxId = 'rating-dist-chart'
    let canvas = document.getElementById(ctxId)
    if (charts[ctxId]) charts[ctxId].destroy()
    
    charts[ctxId] = new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['1','2','3','4','5','6','7','8','9','10'],
        datasets: [{
          label: 'Antal vurderinger',
          data: dist,
          backgroundColor: '#8b5cf6'
        }]
      },
      options: {
        scales: { y: { beginAtZero: true } },
        plugins: { legend: { display: true } }
      }
    })
  }

  function renderYearCountsChart(yearCounts, yearsAgg) {
    const ctxId = 'ratings-per-year-chart'
    let canvas = document.getElementById(ctxId)
    if (charts[ctxId]) charts[ctxId].destroy()

    // Sort by year
    const sortedYears = Object.keys(yearCounts).sort()
    const data = sortedYears.map(y => yearCounts[y])

    charts[ctxId] = new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: sortedYears,
        datasets: [{
          label: 'Antal vurderinger',
          data: data,
          backgroundColor: '#a78bfa'
        }]
      },
      options: {
        scales: { y: { beginAtZero: true } },
        plugins: { legend: { display: true } }
      }
    })
  }

  function renderYearAvgChart(yearAvgRatings, yearsAgg) {
    const ctxId = 'avg-rating-per-year-chart'
    let canvas = document.getElementById(ctxId)
    if (charts[ctxId]) charts[ctxId].destroy()

    const sortedYears = Object.keys(yearAvgRatings).sort()
    const data = sortedYears.map(y => parseFloat(yearAvgRatings[y]))

    charts[ctxId] = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: sortedYears,
        datasets: [{
          label: 'Gns. vurdering',
          data: data,
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          tension: 0.3,
          fill: true
        }]
      },
      options: {
        scales: { y: { min: 0, max: 10 } },
        plugins: { legend: { display: true } }
      }
    })
  }

  function escapeHtml(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') }

  reviewerFilter.addEventListener('change', () => renderAll(reviewerFilter.value))

  loadReviewers().then(() => { buildHeader(); renderAll() })
})
