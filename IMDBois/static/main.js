document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('search')
  const suggestions = document.getElementById('suggestions')
  const reviewerSelect = document.getElementById('reviewer')
  const rating = document.getElementById('rating')
  const submit = document.getElementById('submit')
  const msg = document.getElementById('message')
  const selectedMovie = document.getElementById('selected-movie')

  for (let i = 1; i <= 10; i++) {
    const opt = document.createElement('option')
    opt.value = i
    opt.textContent = i
    rating.appendChild(opt)
  }

  let timer = null
  let selectedTmdbId = null
  let selectedTitle = null
  search.addEventListener('input', () => {
    clearTimeout(timer)
    selectedTmdbId = null
    selectedTitle = null
    submit.disabled = true
    selectedMovie.innerHTML = '<p>Vælg en film fra søgeresultaterne for at se detaljer.</p>'
    const q = search.value.trim()
    if (!q) { suggestions.innerHTML = ''; return }
    timer = setTimeout(() => fetchSuggestions(q), 300)
  })

  suggestions.addEventListener('click', (e) => {
    const target = e.target.closest('li.suggestion-card')
    if (!target) return
    const title = target.dataset.title
    const tmdb = target.dataset.tmdb || null
    const overview = target.dataset.overview || ''
    const poster = target.dataset.poster || ''
    const year = target.dataset.year || ''
    search.value = title
    selectedTmdbId = tmdb
    selectedTitle = title
    if (reviewerSelect.value) {
      submit.disabled = false
    }
    suggestions.innerHTML = ''
    selectedMovie.innerHTML = `
      <div class="movie-card">
        ${poster ? `<img src="${escapeHtml(poster)}" alt="${escapeHtml(title)} poster" />` : '<div class="poster-placeholder">?</div>'}
        <div class="movie-meta">
          <h3>${escapeHtml(title)}</h3>
          ${year ? `<p class="movie-year">${escapeHtml(year)}</p>` : ''}
          ${overview ? `<p class="movie-overview">${escapeHtml(overview)}</p>` : '<p>Ingen beskrivelse tilgængelig.</p>'}
        </div>
      </div>
    `
  })

  function updateSubmitState() {
    submit.disabled = !(selectedTitle && reviewerSelect.value && rating.value)
  }

  reviewerSelect.addEventListener('change', updateSubmitState)
  rating.addEventListener('change', updateSubmitState)

  submit.addEventListener('click', async () => {
    const title = search.value.trim()
    const reviewer = reviewerSelect.value
    const r = rating.value
    msg.textContent = ''
    if (!title || !reviewer || !r) { msg.textContent = 'Angiv venligst film, anmelder og vurdering.'; return }
    try {
      if (!selectedTitle) {
        msg.textContent = 'Vælg venligst en film fra søgeresultaterne, før du sender vurderingen.'
        return
      }
      const res = await fetch('/api/rate', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title: selectedTitle, reviewer, rating: r, tmdb_id: selectedTmdbId})
      })
      const data = await res.json()
      if (res.ok) {
        msg.textContent = `Gemt: ${data.title} (gennemsnit ${data.avg}, ${data.count} vurderinger)`
      } else {
        msg.textContent = data.error || 'Fejl under lagring'
      }
    } catch (err) {
      msg.textContent = 'Netværksfejl. Prøv igen.'
    }
  })

  async function fetchSuggestions(q) {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`)
      const arr = await res.json()
      suggestions.innerHTML = arr.map(a => {
        const image = a.poster_path ? `<img src="${escapeHtml(a.poster_path)}" alt="${escapeHtml(a.title)} poster" onerror="this.onerror=null;this.src='/static/poster-placeholder.svg';" />` : '<div class="poster-placeholder">?</div>'
        const year = a.release_date ? ` <span class="movie-year">(${escapeHtml(a.release_date.slice(0,4))})</span>` : ''
        const overview = a.overview ? `<p class="movie-overview">${escapeHtml(a.overview.slice(0,100))}${a.overview.length > 100 ? '...' : ''}</p>` : ''
        return `
          <li class="suggestion-card" data-title="${escapeHtml(a.title)}" data-tmdb="${a.tmdb_id||''}" data-year="${a.release_date?escapeHtml(a.release_date.slice(0,4)) : ''}" data-overview="${escapeHtml(a.overview||'')}" data-poster="${escapeHtml(a.poster_path||'')}">
            <div class="poster">${image}</div>
            <div class="movie-info">
              <strong>${escapeHtml(a.title)}</strong>${year}
              ${overview}
            </div>
          </li>
        `
      }).join('')
    } catch (err) {
      suggestions.innerHTML = ''
    }
  }

  function escapeHtml(s){ return (s+'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;') }
})
