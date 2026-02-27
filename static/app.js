/* ── Accord → glow mapping ───────────────────────────────────────── */
const ACCORD_GLOW = {
  woody: 'woody', wood: 'woody', sandalwood: 'woody', cedar: 'woody', oud: 'woody', amber: 'oriental',
  floral: 'floral', rose: 'floral', jasmine: 'floral', powdery: 'floral',
  fresh: 'fresh', clean: 'fresh', soapy: 'fresh',
  oriental: 'oriental', warm: 'oriental', resinous: 'oriental', balsamic: 'oriental', vanilla: 'gourmand',
  citrus: 'citrus', lemon: 'citrus', bergamot: 'citrus', orange: 'citrus',
  musk: 'musk', white_musk: 'musk',
  green: 'green', herbal: 'green', aromatic: 'green', earthy: 'green',
  aquatic: 'aquatic', marine: 'aquatic', ozonic: 'aquatic',
  gourmand: 'gourmand', sweet: 'gourmand', caramel: 'gourmand', chocolate: 'gourmand',
  spicy: 'spicy', pepper: 'spicy', cinnamon: 'spicy', smoky: 'spicy',
};

const ACCORD_COLORS = {
  woody:    '#b47838',
  floral:   '#dc78a0',
  fresh:    '#50b4dc',
  oriental: '#c86438',
  citrus:   '#e6c83c',
  musk:     '#b4a0c8',
  green:    '#50b464',
  aquatic:  '#3ca0dc',
  gourmand: '#d28c50',
  spicy:    '#d25038',
};

function getGlow(p) {
  const accords = p.main_accords || [];
  for (const a of accords) {
    const key = a.toLowerCase().replace(/\s+/g, '_');
    if (ACCORD_GLOW[key]) return ACCORD_GLOW[key];
    for (const k of Object.keys(ACCORD_GLOW)) {
      if (key.includes(k)) return ACCORD_GLOW[k];
    }
  }
  return null;
}

/* ── State ───────────────────────────────────────────────────────── */
const state = {
  page: 1,
  limit: 24,
  search: '',
  brand: '',
  category: '',
  gender: '',
  notes: [],
  seasons: [],
  accords: [],
  price: '',
  longevities: [],
  sillages: [],
  sort: 'rating',
  order: 'desc',
  total: 0,
  debounceTimer: null,
  currentView: 'explore',
  mapLoaded: false,
};

/* ── DOM refs ────────────────────────────────────────────────────── */
const grid         = document.getElementById('perfumeGrid');
const spinner      = document.getElementById('loadingSpinner');
const emptyState   = document.getElementById('emptyState');
const pagination   = document.getElementById('pagination');
const resultsCount = document.getElementById('resultsCount');
const modalOverlay = document.getElementById('modalOverlay');
const modal        = document.getElementById('modal');
const modalInner   = document.getElementById('modalInner');
const modalClose   = document.getElementById('modalClose');

/* ── Theme ───────────────────────────────────────────────────────── */
function initTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  setTheme(saved);
  document.getElementById('themeToggle').addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(current === 'dark' ? 'light' : 'dark');
  });
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  document.getElementById('themeToggle').textContent = theme === 'dark' ? '○' : '☽';
}

/* ── View switching ──────────────────────────────────────────────── */
function showView(view) {
  state.currentView = view;
  document.getElementById('exploreView').classList.toggle('active', view === 'explore');
  document.getElementById('mapView').classList.toggle('active', view === 'map');
  document.getElementById('navExplore').classList.toggle('active', view === 'explore');
  document.getElementById('navMap').classList.toggle('active', view === 'map');

  if (view === 'map' && !state.mapLoaded) {
    state.mapLoaded = true;
    loadFragranceMap();
  }
}

/* ── Init ────────────────────────────────────────────────────────── */
async function init() {
  initTheme();
  await loadStats();
  await loadBrands();
  await loadNotes();
  await loadAccords();
  await fetchAndRender();
  bindEvents();
}

/* ── API helpers ─────────────────────────────────────────────────── */
async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/* ── Load stats ──────────────────────────────────────────────────── */
async function loadStats() {
  try {
    const s = await api('/api/stats');
    document.getElementById('statPerfumes').textContent = s.total_perfumes.toLocaleString();
    document.getElementById('statBrands').textContent = s.total_brands;
    document.getElementById('statNotes').textContent = s.total_notes;
  } catch (e) { /* silent */ }
}

/* ── Load brands ─────────────────────────────────────────────────── */
async function loadBrands() {
  try {
    const brands = await api('/api/brands');
    const sel = document.getElementById('brandFilter');
    brands.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.name;
      opt.textContent = `${b.name} (${b.count})`;
      sel.appendChild(opt);
    });
  } catch (e) { /* silent */ }
}

/* ── Load accords datalist ──────────────────────────────────────── */
async function loadAccords() {
  try {
    const accords = await api('/api/accords');
    const dl = document.getElementById('accordsList');
    accords.forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.name;
      dl.appendChild(opt);
    });
  } catch (e) { /* silent */ }
}

/* ── Load notes datalist ────────────────────────────────────────── */
async function loadNotes() {
  try {
    const notes = await api('/api/notes');
    const dl = document.getElementById('notesList');
    notes.forEach(n => {
      const opt = document.createElement('option');
      opt.value = n;
      dl.appendChild(opt);
    });
  } catch (e) { /* silent */ }
}

/* ── Fetch & render ──────────────────────────────────────────────── */
async function fetchAndRender() {
  showLoading(true);
  grid.innerHTML = '';
  emptyState.style.display = 'none';

  const params = new URLSearchParams({
    page: state.page,
    limit: state.limit,
    sort: state.sort,
    order: state.order,
  });
  if (state.search)    params.set('search', state.search);
  if (state.brand)     params.set('brand', state.brand);
  if (state.category)  params.set('category', state.category);
  if (state.gender)    params.set('gender', state.gender);
  state.notes.forEach(n => params.append('note', n));
  state.seasons.forEach(s => params.append('season', s));
  state.accords.forEach(a => params.append('accord', a));
  if (state.price)     params.set('price', state.price);
  state.longevities.forEach(l => params.append('longevity', l));
  state.sillages.forEach(s => params.append('sillage', s));

  try {
    const data = await api(`/api/perfumes?${params}`);
    state.total = data.total;
    showLoading(false);
    updateResultsBar(data.total);

    if (data.perfumes.length === 0) {
      emptyState.style.display = 'block';
    } else {
      data.perfumes.forEach((p, i) => {
        const card = buildCard(p, i);
        grid.appendChild(card);
      });
    }
    renderPagination(data.total);
  } catch (e) {
    showLoading(false);
    emptyState.style.display = 'block';
    console.error(e);
  }
}

/* ── Build card ──────────────────────────────────────────────────── */
function buildCard(p, index) {
  const card = document.createElement('div');
  card.className = 'perfume-card';
  card.style.animationDelay = `${Math.min(index, 15) * 60}ms`;

  const glow = getGlow(p);
  if (glow) card.setAttribute('data-glow', glow);

  const allNotes = [
    ...(p.top_notes || []),
    ...(p.middle_notes || []),
    ...(p.base_notes || []),
  ];
  const topNotes = allNotes.slice(0, 3);
  const stars = ratingToStars(p.rating);
  const imgSrc = p.image_path || p.image_url || '';
  const dotColor = glow ? ACCORD_COLORS[glow] : null;

  card.innerHTML = `
    <div class="card-image-wrap">
      <img class="card-image" src="${esc(imgSrc)}" alt="${esc(p.name)}" loading="lazy"
           onerror="this.style.opacity='0'" />
      ${p.category ? `<span class="card-category">${esc(p.category)}</span>` : ''}
      ${dotColor ? `<span class="card-accord-dot" style="background:${dotColor}" title="${(p.main_accords||[])[0]||''}"></span>` : ''}
      ${p.gender ? `<span class="card-gender">${esc(p.gender)}</span>` : ''}
    </div>
    <div class="card-body">
      <div class="card-brand">${esc(p.brand || '')}</div>
      <div class="card-name">${esc(p.name || '')}</div>
      <div class="card-meta">
        <div class="card-rating">
          <span class="rating-value">${p.rating ? p.rating.toFixed(2) : '—'}</span>
          <div class="rating-stars">${stars}</div>
        </div>
        <span class="card-votes">${p.votes ? formatVotes(p.votes) : ''}</span>
      </div>
      ${topNotes.length ? `
        <div class="card-notes">
          ${topNotes.map(n => `<span class="note-tag">${esc(n)}</span>`).join('')}
          ${allNotes.length > 3 ? `<span class="note-tag">+${allNotes.length - 3}</span>` : ''}
        </div>` : ''}
    </div>`;

  card.addEventListener('click', () => openModal(p));
  return card;
}

/* ── Modal ───────────────────────────────────────────────────────── */
function openModal(p) {
  const imgSrc = p.image_path || p.image_url || '';
  const topNotes    = p.top_notes    || [];
  const middleNotes = p.middle_notes || [];
  const baseNotes   = p.base_notes   || [];
  const allNotes    = [...topNotes, ...middleNotes, ...baseNotes];
  const hasLayers   = topNotes.length || middleNotes.length || baseNotes.length;
  const glow        = getGlow(p);
  const glowColor   = glow ? ACCORD_COLORS[glow] : null;

  let notesHtml = '';
  if (hasLayers) {
    if (topNotes.length)    notesHtml += noteGroup('Top Notes',   topNotes,    'top');
    if (middleNotes.length) notesHtml += noteGroup('Heart Notes', middleNotes, 'middle');
    if (baseNotes.length)   notesHtml += noteGroup('Base Notes',  baseNotes,   'base');
  } else if (allNotes.length) {
    notesHtml += noteGroup('Notes', allNotes, 'top');
  }

  const accordsHtml = (p.main_accords || []).length
    ? `<div class="modal-accords">${p.main_accords.map(a =>
        `<span class="modal-accord-tag"${glowColor ? ` style="border-color:${glowColor}40;color:${glowColor}"` : ''}>${esc(a)}</span>`
      ).join('')}</div>`
    : '';

  const voteBarsHtml = buildVoteIcons(p);

  modalInner.innerHTML = `
    <div class="modal-image-col"${glowColor ? ` style="background:color-mix(in srgb, ${glowColor} 6%, var(--surface-2))"` : ''}>
      <img class="modal-image" src="${esc(imgSrc)}" alt="${esc(p.name)}"
           onerror="this.style.opacity='0'" />
      ${accordsHtml}
    </div>
    <div class="modal-content-col">
      <div class="modal-eyebrow">${esc(p.brand || '')}</div>
      <div class="modal-name">${esc(p.name || '')}</div>
      <div class="modal-meta-row">
        ${p.rating ? `<span class="modal-rating-big">${p.rating.toFixed(2)}</span>` : ''}
        ${p.votes  ? `<span class="modal-votes">${p.votes.toLocaleString()} votes</span>` : ''}
        ${p.gender ? `<span class="modal-gender">${esc(p.gender)}</span>` : ''}
        ${p.release_year ? `<span class="modal-year">${p.release_year}</span>` : ''}
      </div>
      ${voteBarsHtml ? `<hr class="modal-divider" />${voteBarsHtml}` : ''}
      ${notesHtml ? `<hr class="modal-divider" />${notesHtml}` : ''}
      ${p.description ? `
        <hr class="modal-divider" />
        <div class="modal-section-title">About</div>
        <p class="modal-description">${esc(p.description)}</p>` : ''}
      ${p.url ? `<a class="modal-link" href="${p.url}" target="_blank" rel="noopener">View on Fragrantica →</a>` : ''}
    </div>`;

  modalOverlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

/* ── Vote icon helpers ───────────────────────────────────────────── */
// Returns {key, pct}[] sorted desc for a vote object
function voteRanked(obj) {
  if (!obj || typeof obj !== 'object') return [];
  const entries = Object.entries(obj);
  const total = entries.reduce((s, [, v]) => s + v, 0);
  if (!total) return [];
  return entries
    .map(([k, v]) => ({ key: k, pct: Math.round(v / total * 100) }))
    .sort((a, b) => b.pct - a.pct);
}

function topVote(obj) {
  const r = voteRanked(obj);
  return r.length ? r[0] : null;
}

// Longevity: 5 fill-bars (very_weak → eternal)
function longevityHtml(obj) {
  const LEVELS = ['very_weak', 'weak', 'moderate', 'long_lasting', 'eternal'];
  const LABELS = { very_weak: 'Very Weak', weak: 'Weak', moderate: 'Moderate', long_lasting: 'Long Lasting', eternal: 'Eternal' };
  const ranked = voteRanked(obj);
  if (!ranked.length) return '';
  const topKey = ranked[0].key;
  const topIdx = LEVELS.indexOf(topKey);

  const bars = LEVELS.map((lvl, i) => {
    const active = i <= topIdx;
    return `<div class="vi-bar${active ? ' active' : ''}"></div>`;
  }).join('');

  return `<div class="vote-icon-block">
    <div class="vi-label">Longevity</div>
    <div class="vi-longevity-bars">${bars}</div>
    <div class="vi-top-label">${LABELS[topKey] || topKey.replace(/_/g,' ')}</div>
  </div>`;
}

// Sillage: 4 wave arcs (intimate → enormous)
function sillageHtml(obj) {
  const LEVELS = ['intimate', 'moderate', 'strong', 'enormous'];
  const LABELS = { intimate: 'Intimate', moderate: 'Moderate', strong: 'Strong', enormous: 'Enormous' };
  const ranked = voteRanked(obj);
  if (!ranked.length) return '';
  const topKey = ranked[0].key;
  const topIdx = LEVELS.indexOf(topKey);

  // SVG wave arcs - each arc becomes active up to topIdx
  const arcs = LEVELS.map((lvl, i) => {
    const r = 6 + i * 7;
    const active = i <= topIdx;
    return `<circle cx="20" cy="20" r="${r}" fill="none" stroke-width="2.2"
      stroke="${active ? 'currentColor' : 'var(--border-2)'}"
      opacity="${active ? 1 : 0.35}"
      stroke-dasharray="${Math.PI * r * 0.6} ${Math.PI * r}"
      stroke-dashoffset="${-Math.PI * r * 0.2}"
      stroke-linecap="round" />`;
  }).join('');

  return `<div class="vote-icon-block">
    <div class="vi-label">Sillage</div>
    <div class="vi-sillage-wrap">
      <svg viewBox="0 0 40 40" class="vi-sillage-svg">${arcs}</svg>
    </div>
    <div class="vi-top-label">${LABELS[topKey] || topKey.replace(/_/g,' ')}</div>
  </div>`;
}

// Price Value: coin icons (1–5, way_overpriced=1 coin active, great_value=5 coins)
function priceHtml(obj) {
  const LEVELS = ['way_overpriced', 'overpriced', 'ok', 'good_value', 'great_value'];
  const LABELS = { way_overpriced: 'Overpriced', overpriced: 'Pricey', ok: 'Fair', good_value: 'Good Value', great_value: 'Great Value' };
  const ranked = voteRanked(obj);
  if (!ranked.length) return '';
  const topKey = ranked[0].key;
  const topIdx = LEVELS.indexOf(topKey);
  // 1 coin = way_overpriced, 5 coins = great_value
  const activeCoins = topIdx + 1;

  const coins = Array.from({length: 5}, (_, i) =>
    `<span class="vi-coin${i < activeCoins ? ' active' : ''}">◉</span>`
  ).join('');

  return `<div class="vote-icon-block">
    <div class="vi-label">Value</div>
    <div class="vi-coins">${coins}</div>
    <div class="vi-top-label">${LABELS[topKey] || topKey.replace(/_/g,' ')}</div>
  </div>`;
}

// Season: 4 season icons + day/night — each group normalized independently
function seasonHtml(obj) {
  if (!obj || typeof obj !== 'object') return '';

  const SEASONS = [
    { key: 'spring', icon: '🌸', label: 'Spring' },
    { key: 'summer', icon: '☀️', label: 'Summer' },
    { key: 'fall',   icon: '🍂', label: 'Fall'   },
    { key: 'winter', icon: '❄️', label: 'Winter' },
  ];
  const DAYTIME = [
    { key: 'day',   icon: '🌤', label: 'Day'   },
    { key: 'night', icon: '🌙', label: 'Night' },
  ];

  // Compute max within each group separately
  const seasonMax  = Math.max(...SEASONS.map(s => obj[s.key] || 0));
  const daytimeMax = Math.max(...DAYTIME.map(s => obj[s.key] || 0));

  function makeIcon(item, groupMax) {
    const val = obj[item.key] || 0;
    const rel = groupMax > 0 ? val / groupMax : 0;
    const pct = groupMax > 0 ? Math.round(val / groupMax * 100) : 0;
    const active = rel >= 0.55;
    return `<div class="vi-season-item${active ? ' active' : ''}" title="${item.label}: ${pct}%">
      <span class="vi-season-icon">${item.icon}</span>
      <span class="vi-season-name">${item.label}</span>
    </div>`;
  }

  return `<div class="vote-icon-block vi-season-block">
    <div class="vi-label">Season</div>
    <div class="vi-season-row">${SEASONS.map(s => makeIcon(s, seasonMax)).join('')}</div>
    <div class="vi-season-row vi-daytime-row">${DAYTIME.map(s => makeIcon(s, daytimeMax)).join('')}</div>
  </div>`;
}

function buildVoteIcons(p) {
  const lon = longevityHtml(p.longevity);
  const sil = sillageHtml(p.sillage);
  const pri = priceHtml(p.price_value);
  const sea = seasonHtml(p.season);
  if (!lon && !sil && !pri && !sea) return '';
  return `<div class="vote-icons-grid">
    ${lon}${sil}${pri}${sea}
  </div>`;
}

function noteGroup(label, notes, type) {
  return `
    <div class="modal-notes-group">
      <div class="modal-section-title">${label}</div>
      <div class="modal-notes-row">
        ${notes.map(n => {
          const noteSlug = n.replace(/ /g, '_');
          const noteImgUrl = `/note_images/${noteSlug}.png`;
          return `<span class="modal-note-tag ${type}" data-note-img="${noteImgUrl}">${esc(n)}</span>`;
        }).join('')}
      </div>
    </div>`;
}

function closeModal() {
  modalOverlay.classList.remove('open');
  document.body.style.overflow = '';
}

/* ── Fragrance Map ───────────────────────────────────────────────── */
async function loadFragranceMap() {
  const accordGrid = document.getElementById('accordGrid');
  try {
    const data = await api('/api/perfumes?limit=1000&sort=rating&order=desc');
    const perfumes = data.perfumes || [];

    // Group by dominant accord
    const groups = {};
    for (const p of perfumes) {
      if (!p.main_accords || !p.main_accords.length) continue;
      const raw = p.main_accords[0];
      const key = raw.toLowerCase().trim();
      let bucket = null;
      // Map to a canonical bucket
      for (const [k] of Object.entries(ACCORD_GLOW)) {
        if (key.includes(k)) { bucket = ACCORD_GLOW[k]; break; }
      }
      if (!bucket) bucket = 'other';
      if (bucket === 'other') continue;
      if (!groups[bucket]) groups[bucket] = [];
      // deduplicate by name
      if (!groups[bucket].find(x => x.name === p.name && x.brand === p.brand)) {
        groups[bucket].push(p);
      }
    }

    // Sort groups by count desc
    const sorted = Object.entries(groups)
      .filter(([, arr]) => arr.length >= 3)
      .sort((a, b) => b[1].length - a[1].length);

    accordGrid.innerHTML = '';
    for (const [accordType, items] of sorted) {
      const top5 = items.sort((a, b) => (b.rating || 0) - (a.rating || 0)).slice(0, 5);
      const color = ACCORD_COLORS[accordType] || '#888';
      const label = accordType.charAt(0).toUpperCase() + accordType.slice(1);

      const section = document.createElement('div');
      section.className = 'accord-section';
      section.innerHTML = `
        <div class="accord-header">
          <span class="accord-color-dot" style="background:${color}"></span>
          <span class="accord-name">${label}</span>
          <span class="accord-count">${items.length} fragrances</span>
        </div>
        <div class="accord-perfume-list">
          ${top5.map((p, i) => {
            const img = p.image_path || p.image_url || '';
            return `<div class="accord-perfume-row" data-idx="${i}">
              <span class="accord-perfume-rank">${i + 1}</span>
              <img class="accord-perfume-img" src="${esc(img)}" alt="" onerror="this.style.opacity='0'" loading="lazy" />
              <div class="accord-perfume-info">
                <div class="accord-perfume-name">${esc(p.name)}</div>
                <div class="accord-perfume-brand">${esc(p.brand || '')}</div>
              </div>
              <span class="accord-perfume-rating">${p.rating ? p.rating.toFixed(2) : '—'}</span>
            </div>`;
          }).join('')}
        </div>`;

      // click rows to open modal
      top5.forEach((p, i) => {
        section.querySelectorAll('.accord-perfume-row')[i]
          .addEventListener('click', () => openModal(p));
      });

      accordGrid.appendChild(section);
    }
  } catch (e) {
    accordGrid.innerHTML = '<p style="color:var(--text-3);padding:32px">Could not load fragrance map.</p>';
    console.error(e);
  }
}

/* ── Pagination ──────────────────────────────────────────────────── */
function renderPagination(total) {
  const totalPages = Math.ceil(total / state.limit);
  pagination.innerHTML = '';
  if (totalPages <= 1) return;

  const prev = btn('‹', state.page === 1, () => go(state.page - 1));
  pagination.appendChild(prev);

  const range = pageRange(state.page, totalPages);
  range.forEach(p => {
    if (p === '…') {
      const el = document.createElement('span');
      el.textContent = '…';
      el.style.cssText = 'padding:0 6px;color:var(--text-3);line-height:36px;';
      pagination.appendChild(el);
    } else {
      const b = btn(p, false, () => go(p));
      if (p === state.page) b.classList.add('active');
      pagination.appendChild(b);
    }
  });

  const next = btn('›', state.page === totalPages, () => go(state.page + 1));
  pagination.appendChild(next);
}

function btn(label, disabled, onClick) {
  const b = document.createElement('button');
  b.className = 'page-btn' + (disabled ? ' disabled' : '');
  b.textContent = label;
  if (!disabled) b.addEventListener('click', onClick);
  return b;
}

function go(page) {
  state.page = page;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  fetchAndRender();
}

function pageRange(current, total) {
  if (total <= 7) return Array.from({length: total}, (_, i) => i + 1);
  const pages = [1];
  if (current > 3) pages.push('…');
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
  if (current < total - 2) pages.push('…');
  pages.push(total);
  return pages;
}

/* ── Helpers ─────────────────────────────────────────────────────── */
function ratingToStars(rating) {
  if (!rating) return '';
  const pct = (rating - 1) / 4;
  const filled = Math.round(pct * 5);
  return Array.from({length: 5}, (_, i) =>
    `<span class="star ${i < filled ? 'filled' : ''}">★</span>`
  ).join('');
}

function formatVotes(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'm';
  if (n >= 1000)    return (n / 1000).toFixed(1) + 'k';
  return n.toString();
}

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function showLoading(show) {
  spinner.style.display = show ? 'flex' : 'none';
}

function updateResultsBar(total) {
  const start = (state.page - 1) * state.limit + 1;
  const end   = Math.min(state.page * state.limit, total);
  resultsCount.textContent = total > 0
    ? `Showing ${start}–${end} of ${total.toLocaleString()} fragrances`
    : '';
}

/* ── Events ──────────────────────────────────────────────────────── */
function bindEvents() {
  document.getElementById('searchInput').addEventListener('input', e => {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(() => {
      state.search = e.target.value.trim();
      state.page = 1;
      fetchAndRender();
    }, 350);
  });

  document.getElementById('brandFilter').addEventListener('change', e => {
    state.brand = e.target.value;
    state.page = 1;
    fetchAndRender();
  });

  document.getElementById('categoryFilter').addEventListener('change', e => {
    state.category = e.target.value;
    state.page = 1;
    fetchAndRender();
  });

  document.getElementById('genderFilter').addEventListener('change', e => {
    state.gender = e.target.value;
    state.page = 1;
    fetchAndRender();
  });

  // Note input with chips
  const noteInput = document.getElementById('noteInput');
  const selectedNotesContainer = document.getElementById('selectedNotes');
  noteInput.addEventListener('change', e => {
    const val = e.target.value.trim();
    if (val && !state.notes.includes(val)) {
      state.notes.push(val);
      renderSelectedChips('notes');
      state.page = 1;
      fetchAndRender();
    }
    noteInput.value = '';
  });

  // Accord input with chips
  const accordInput = document.getElementById('accordInput');
  const selectedAccordsContainer = document.getElementById('selectedAccords');
  accordInput.addEventListener('change', e => {
    const val = e.target.value.trim();
    if (val && !state.accords.includes(val)) {
      state.accords.push(val);
      renderSelectedChips('accords');
      state.page = 1;
      fetchAndRender();
    }
    accordInput.value = '';
  });

  document.getElementById('sortSelect').addEventListener('change', e => {
    const [sort, order] = e.target.value.split('-');
    state.sort = sort;
    state.order = order;
    state.page = 1;
    fetchAndRender();
  });

  // Accord filter removed - now using chips in HTML

  // Season chips (multi-select)
  document.querySelectorAll('.season-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const s = chip.getAttribute('data-season');
      const idx = state.seasons.indexOf(s);
      if (idx > -1) {
        state.seasons.splice(idx, 1);
        chip.classList.remove('active');
      } else {
        state.seasons.push(s);
        chip.classList.add('active');
      }
      state.page = 1;
      fetchAndRender();
    });
  });

  // Generic filter chips (longevity, sillage - multi-select, price - single)
  document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const filterKey = chip.getAttribute('data-filter');
      const val = chip.getAttribute('data-value');
      
      if (filterKey === 'longevity') {
        const idx = state.longevities.indexOf(val);
        if (idx > -1) {
          state.longevities.splice(idx, 1);
          chip.classList.remove('active');
        } else {
          state.longevities.push(val);
          chip.classList.add('active');
        }
      } else if (filterKey === 'sillage') {
        const idx = state.sillages.indexOf(val);
        if (idx > -1) {
          state.sillages.splice(idx, 1);
          chip.classList.remove('active');
        } else {
          state.sillages.push(val);
          chip.classList.add('active');
        }
      } else if (filterKey === 'price') {
        if (state.price === val) {
          state.price = '';
          chip.classList.remove('active');
        } else {
          state.price = val;
          document.querySelectorAll('.filter-chip[data-filter="price"]')
            .forEach(c => c.classList.remove('active'));
          chip.classList.add('active');
        }
      }
      state.page = 1;
      fetchAndRender();
    });
  });

  document.getElementById('clearFilters').addEventListener('click', () => {
    state.search = '';
    state.brand = '';
    state.category = '';
    state.gender = '';
    state.notes = [];
    state.seasons = [];
    state.accords = [];
    state.price = '';
    state.longevities = [];
    state.sillages = [];
    state.sort = 'rating';
    state.order = 'desc';
    state.page = 1;
    document.getElementById('searchInput').value = '';
    document.getElementById('brandFilter').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('genderFilter').value = '';
    renderSelectedChips('notes');
    renderSelectedChips('accords');
    document.getElementById('sortSelect').value = 'rating-desc';
    document.querySelectorAll('.season-chip, .filter-chip').forEach(c => c.classList.remove('active'));
    fetchAndRender();
  });

  modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', e => {
    if (e.target === modalOverlay) closeModal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });

  // Note tooltip
  setupNoteTooltips();
}

/* ── Render selected chips ───────────────────────────────────────── */
function renderSelectedChips(type) {
  const container = type === 'notes' 
    ? document.getElementById('selectedNotes')
    : document.getElementById('selectedAccords');
  const items = type === 'notes' ? state.notes : state.accords;
  
  container.innerHTML = '';
  items.forEach(item => {
    const chip = document.createElement('div');
    chip.className = 'selected-chip';
    chip.innerHTML = `
      <span>${esc(item)}</span>
      <span class="selected-chip-remove">×</span>
    `;
    chip.addEventListener('click', () => {
      const idx = items.indexOf(item);
      if (idx > -1) {
        items.splice(idx, 1);
        renderSelectedChips(type);
        state.page = 1;
        fetchAndRender();
      }
    });
    container.appendChild(chip);
  });
}

/* ── Note Tooltips ───────────────────────────────────────────────── */
let noteTooltip = null;

function setupNoteTooltips() {
  // Create tooltip element
  noteTooltip = document.createElement('div');
  noteTooltip.className = 'note-tooltip';
  document.body.appendChild(noteTooltip);

  // Delegate hover events
  document.addEventListener('mouseover', e => {
    const tag = e.target.closest('.modal-note-tag[data-note-img]');
    if (tag) showNoteTooltip(tag, e);
  });

  document.addEventListener('mouseout', e => {
    const tag = e.target.closest('.modal-note-tag[data-note-img]');
    if (tag) hideNoteTooltip();
  });

  document.addEventListener('mousemove', e => {
    if (noteTooltip.classList.contains('show')) {
      positionTooltip(e);
    }
  });
}

function showNoteTooltip(tag, e) {
  const imgUrl = tag.getAttribute('data-note-img');
  const noteName = tag.textContent.trim();
  
  noteTooltip.innerHTML = `
    <img class="note-tooltip-img" src="${imgUrl}" alt="${noteName}" 
         onerror="this.style.display='none'" />
    <div class="note-tooltip-name">${noteName}</div>
  `;
  
  positionTooltip(e);
  setTimeout(() => noteTooltip.classList.add('show'), 10);
}

function hideNoteTooltip() {
  noteTooltip.classList.remove('show');
}

function positionTooltip(e) {
  const offset = 15;
  let x = e.clientX + offset;
  let y = e.clientY + offset;
  
  // Keep tooltip within viewport
  const rect = noteTooltip.getBoundingClientRect();
  if (x + rect.width > window.innerWidth) {
    x = e.clientX - rect.width - offset;
  }
  if (y + rect.height > window.innerHeight) {
    y = e.clientY - rect.height - offset;
  }
  
  noteTooltip.style.left = x + 'px';
  noteTooltip.style.top = y + 'px';
}

/* ── Start ───────────────────────────────────────────────── */
init();
