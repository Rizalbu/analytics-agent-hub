/* Growth Command Hub · SPA controller (vanilla JS, no build step).
   Sections: utils · ECharts theme · state/API · pages · chat · cmdk · tour. */
'use strict';

// ---------- utils ----------
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const fmtInt = n => n == null ? '–' : Math.round(n).toLocaleString('id-ID');
const rp = n => {
  if (n == null) return '–';
  const a = Math.abs(n);
  if (a >= 1e9) return 'Rp ' + (n / 1e9).toFixed(2) + ' M';
  if (a >= 1e6) return 'Rp ' + (n / 1e6).toFixed(1) + ' jt';
  if (a >= 1e3) return 'Rp ' + (n / 1e3).toFixed(0) + ' rb';
  return 'Rp ' + fmtInt(n);
};
const pct = n => n == null ? '–' : n + '%';
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  let [resource, config] = args;
  const url = typeof resource === 'string' ? resource : (resource && resource.url) || '';
  const isApi = url.startsWith('/api') || url.startsWith(location.origin + '/api');
  const token = sessionStorage.getItem('grc-token');
  const orgId = sessionStorage.getItem('grc-org');
  if (isApi && token) {
    config = config || {};
    config.headers = { ...config.headers, Authorization: `Bearer ${token}` };
    if (orgId && !url.includes('/api/orgs')) config.headers['X-Org-Id'] = orgId;
  }
  return originalFetch(resource, config);
};
const api = async (path, options = {}) => {
  const r = await fetch(path, options); 
  if (!r.ok) throw new Error(r.status); 
  return r.json(); 
};
const mdInline = s => (s || '').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`(.+?)`/g, '<code>$1</code>').replace(/\n/g, '<br>');
const organicTag = () => '<span style="color:var(--text-faint)" title="No ad spend (organic channel)">organic</span>';
const toast = (m) => { const t = el('div', 'toast', m); $('#toasts').append(t); setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 250); }, 2600); };
const timeAgo = (iso) => {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 0) return 'just now';
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + 'm ago';
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return hrs + 'h ago';
  const days = Math.floor(hrs / 24);
  if (days < 30) return days + 'd ago';
  return Math.floor(days / 30) + 'mo ago';
};

// ---------- ECharts theme ----------
const CSS = getComputedStyle(document.documentElement);
const v = n => CSS.getPropertyValue(n).trim();
const SERIES = ['--c1', '--c2', '--c3', '--c4', '--c5', '--c6', '--c7'].map(v);
const charts = new Map();
function chart(node, option, key) {
  if (!node) return;
  const inst = echarts.init(node, null, { renderer: 'canvas' });
  const base = {
    color: SERIES, textStyle: { fontFamily: v('--font'), color: v('--text-dim') },
    grid: { left: 48, right: 20, top: 38, bottom: 34, containLabel: true },
    tooltip: { backgroundColor: v('--surface-3'), borderColor: v('--border-strong'),
      textStyle: { color: v('--text') }, axisPointer: { lineStyle: { color: v('--border-strong') } } },
    legend: { textStyle: { color: v('--text-dim') }, icon: 'roundRect', itemWidth: 10, itemHeight: 10 },
    xAxis: { axisLine: { lineStyle: { color: v('--border') } }, axisLabel: { color: v('--text-faint') },
      splitLine: { show: false }, axisTick: { show: false } },
    yAxis: { axisLine: { show: false }, axisLabel: { color: v('--text-faint') },
      splitLine: { lineStyle: { color: 'rgba(35,40,56,.6)' } }, axisTick: { show: false } },
  };
  inst.setOption(deepMerge(base, option));
  if (key) charts.set(key, inst);
  return inst;
}
function deepMerge(a, b) {
  const out = Array.isArray(a) ? [...a] : { ...a };
  for (const k in b) {
    if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k]) && typeof out[k] === 'object') out[k] = deepMerge(out[k], b[k]);
    else out[k] = b[k];
  }
  return out;
}
window.addEventListener('resize', () => charts.forEach(c => c.resize()));

// ---------- state ----------
const NAV = [
  { id: 'overview', label: 'Overview', icon: 'i-overview', sub: 'Executive scorecard', section: 'Analytics' },
  { id: 'funnel', label: 'Funnel Explorer', icon: 'i-funnel', sub: 'Stage conversion & cohort lag' },
  { id: 'channels', label: 'Channels & Spend', icon: 'i-channel', sub: 'CAC · ROAS · channel mix' },
  { id: 'studios', label: 'Studios', icon: 'i-studio', sub: 'Per-location performance' },
  { id: 'revenue', label: 'Revenue & Targets', icon: 'i-revenue', sub: 'Plan mix & attainment' },
  { id: 'forecast', label: 'Forecast', icon: 'i-forecast', sub: 'Revenue projection & backtest' },
  { id: 'anomalies', label: 'Anomalies', icon: 'i-anomaly', sub: 'Statistical outlier scanner' },
  { id: 'geoflows', label: 'Member Origins', icon: 'i-globe', sub: 'Global member flows & reach' },
  { id: 'agents', label: 'AI Agents', icon: 'i-agents', sub: 'Your AI team workspace', section: 'Workspace' },
  { id: 'sql', label: 'SQL Workspace', icon: 'i-sql', sub: 'Run read-only SQL on the warehouse' },
  { id: 'connectors', label: 'Data Sources', icon: 'i-database', sub: 'Connect databases, warehouses, files & APIs', section: 'Engineering' },
  { id: 'lineage', label: 'Model Lineage', icon: 'i-quality', sub: 'dbt model graph · staging → marts' },
  { id: 'quality', label: 'Data Quality', icon: 'i-quality', sub: 'dbt tests & freshness' },
  { id: 'sheets', label: 'Data Sync', icon: 'i-sheet', sub: 'Governed sync across your sources' },
];
const state = { page: 'overview', meta: null, filters: {} };

// ---------- boot ----------
// ---------- auth gate ----------
(function gate() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) document.body.classList.add('no-motion');
  applyTheme(localStorage.getItem('hub-theme') || 'dark');
  if (sessionStorage.getItem('grc-token')) { $('#login').style.display = 'none'; enterApp(); return; }
  // show login
  $('#login').style.display = 'grid';
  startLoginCanvas();
  const fill = (u, p) => { $('#loginUser').value = u; $('#loginPass').value = p; };
  $$('.login-demo code').forEach((c, i) => c.onclick = () => fill('try', 'tryon'));
  $('#loginForm').onsubmit = async e => {
    e.preventDefault();
    const u = $('#loginUser').value.trim(), p = $('#loginPass').value;
    try {
      const r = await originalFetch('/api/auth/login', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username: u, password: p }),
      });
      if (!r.ok) throw new Error('bad creds');
      const { token } = await r.json();
      sessionStorage.setItem('grc-token', token);
      sessionStorage.setItem('grc-user', u);
      $('#login').classList.add('hide');
      setTimeout(() => { $('#login').style.display = 'none'; }, 520);
      enterApp();
    } catch {
      const card = $('#loginForm'); card.classList.remove('shake'); void card.offsetWidth; card.classList.add('shake');
      const err = $('#loginErr'); err.textContent = 'Incorrect username or password. Try the demo access below.'; err.classList.add('show');
    }
  };
})();

function enterApp() { $('#app').style.display = ''; initApp(); }

async function initApp() {
  if (state.meta) return;            // already initialized
  buildNav();
  try { state.meta = await api('/api/meta'); } catch { state.meta = { cities: [], channels: [], studios: [], months: [], llm: { enabled: false } }; }
  reflectLLM(state.meta.llm || { enabled: false });
  buildFilters();
  wireChrome();
  initChat();
  initAccount();
  initSettings();
  route();
  if (new URLSearchParams(location.search).get('tour') === '1') setTimeout(startTour, 600);
}

// 3D rotating point-globe on the login art (pure canvas, no deps)
function startLoginCanvas() {
  const cv = $('#loginCanvas'); if (!cv) return;
  const ctx = cv.getContext('2d');
  const accent = v('--accent'), accent2 = v('--accent-2'), cyan = v('--info');
  let W, H, dpr = Math.min(2, window.devicePixelRatio || 1);
  const N = 200, pts = [];
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), th = i * 2.399963;
    pts.push({ x: Math.cos(th) * r, y, z: Math.sin(th) * r });
  }
  function size() { W = cv.clientWidth; H = cv.clientHeight; cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); }
  size(); window.addEventListener('resize', size);
  let mx = 0, my = 0, tmx = 0, tmy = 0;
  cv.parentElement.addEventListener('pointermove', e => {
    const r = cv.getBoundingClientRect();
    tmx = ((e.clientX - r.left) / r.width - 0.5) * 0.8; tmy = ((e.clientY - r.top) / r.height - 0.5) * 0.8;
  });
  let a = 0, raf;
  const noMotion = document.body.classList.contains('no-motion');
  function frame() {
    a += 0.0024; mx += (tmx - mx) * 0.05; my += (tmy - my) * 0.05;
    const cx = W * 0.62, cy = H * 0.42, R = Math.min(W, H) * 0.36;
    ctx.clearRect(0, 0, W, H);
    const ay = a + mx, ax = my * 0.6;
    const proj = pts.map(p => {
      let x = p.x, y = p.y, z = p.z;
      let x1 = x * Math.cos(ay) - z * Math.sin(ay), z1 = x * Math.sin(ay) + z * Math.cos(ay);
      let y2 = y * Math.cos(ax) - z1 * Math.sin(ax), z2 = y * Math.sin(ax) + z1 * Math.cos(ax);
      const persp = 1 / (1.8 - z2);
      return { sx: cx + x1 * R * persp * 1.6, sy: cy + y2 * R * persp * 1.6, z: z2, persp };
    });
    // links between near neighbors
    for (let i = 0; i < proj.length; i++) {
      for (let j = i + 1; j < i + 6 && j < proj.length; j++) {
        const dx = proj[i].sx - proj[j].sx, dy = proj[i].sy - proj[j].sy;
        const d = Math.hypot(dx, dy);
        if (d < 70) {
          const op = (1 - d / 70) * 0.22 * Math.max(0, (proj[i].z + proj[j].z) / 2 + 1) / 2;
          ctx.strokeStyle = accent; ctx.globalAlpha = op; ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(proj[i].sx, proj[i].sy); ctx.lineTo(proj[j].sx, proj[j].sy); ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
    proj.forEach((p, i) => {
      const depth = (p.z + 1) / 2;
      const rad = 0.8 + depth * 2.4;
      ctx.fillStyle = i % 7 === 0 ? cyan : (i % 3 === 0 ? accent2 : accent);
      ctx.globalAlpha = 0.25 + depth * 0.6;
      ctx.beginPath(); ctx.arc(p.sx, p.sy, rad, 0, 7); ctx.fill();
    });
    ctx.globalAlpha = 1;
    if (!noMotion) raf = requestAnimationFrame(frame);
  }
  frame();
  if (noMotion) frame();
}

function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  localStorage.setItem('hub-theme', t);
  const use = $('#themeToggle')?.querySelector('use');
  if (use) use.setAttribute('href', t === 'light' ? '#i-sun' : '#i-moon');
  if (state.page && charts.size) route();   // re-render charts with theme colors
}
function reflectLLM(llm) {
  state.llm = llm;
  $('#chatMode').textContent = llm.enabled
    ? `${llm.provider} · ${llm.model}` : 'built-in engine (no key)';
}

function buildNav() {
  const nav = $('#nav'); nav.innerHTML = '';
  NAV.forEach(n => {
    if (n.section) nav.append(el('div', 'nav-section', n.section));
    const item = el('div', 'nav-item', `<svg><use href="#${n.icon}"/></svg><span class="nav-label">${n.label}</span>`);
    item.dataset.page = n.id;
    item.onclick = () => go(n.id);
    nav.append(item);
  });
}

function buildFilters() {
  const m = state.meta, bar = $('#filterBar'); bar.innerHTML = '';
  const mk = (key, label, opts) => {
    const s = el('select', 'select hide-sm');
    s.append(new Option(label, ''));
    opts.forEach(o => s.append(new Option(o.label || o, o.value || o)));
    s.onchange = () => { state.filters[key] = s.value; if (key === 'city') cascadeStudios(); route(); };
    s.dataset.filter = key;
    return s;
  };
  bar.append(mk('city', 'All cities', m.cities));
  bar.append(mk('channel', 'All channels', m.channels));
  bar.append(mk('studio', 'All studios', studioOptions()));
  const months = m.months || [];
  if (months.length) {
    bar.append(mk('month_from', 'From month', months));
    bar.append(mk('month_to', 'To month', months));
  }
}
function studioOptions(city) {
  return (state.meta.studios || [])
    .filter(s => !city || s.city === city)
    .map(s => ({ label: s.studio_code + ' · ' + s.city, value: s.studio_code }));
}
// when a city is picked, narrow the studio dropdown to that city (prevents
// "Arden + a Crestline studio = empty" dead ends)
function cascadeStudios() {
  const sel = $('#filterBar select[data-filter="studio"]'); if (!sel) return;
  const city = state.filters.city;
  const cur = state.filters.studio;
  sel.innerHTML = '';
  sel.append(new Option('All studios', ''));
  studioOptions(city).forEach(o => sel.append(new Option(o.label, o.value)));
  // drop a studio selection that doesn't belong to the new city
  if (cur && !studioOptions(city).some(o => o.value === cur)) { state.filters.studio = ''; sel.value = ''; }
  else sel.value = cur || '';
}

function qs() {
  const p = new URLSearchParams();
  for (const [k, val] of Object.entries(state.filters)) if (val) p.set(k, val);
  return p.toString() ? '?' + p.toString() : '';
}

function go(page) { state.page = page; route(); $('#sidebar').classList.remove('show'); }

function route() {
  const n = NAV.find(x => x.id === state.page) || NAV[0];
  $$('.nav-item').forEach(i => i.classList.toggle('active', i.dataset.page === state.page));
  $('#pageTitle').textContent = n.label;
  $('#pageSub').textContent = n.sub;
  // filters only relevant on analytics pages
  const showFilters = ['overview', 'funnel', 'channels', 'studios'].includes(state.page);
  $('#filterBar').style.display = showFilters ? '' : 'none';
  const c = $('#content'); c.innerHTML = '';
  charts.clear();
  (PAGES[state.page] || PAGES.overview)(c);
}

// ---------- shared render helpers ----------
function card(title, hint, bodyHtml) {
  const c = el('div', 'card');
  if (title) c.append(el('div', 'card-title', `<span>${title}</span>${hint ? `<span class="hint">${hint}</span>` : ''}`));
  if (bodyHtml != null) c.insertAdjacentHTML('beforeend', bodyHtml);
  return c;
}
function chartCard(title, hint, h = '') {
  const c = card(title, hint);
  const node = el('div', 'chart' + (h ? ' ' + h : ''));
  c.append(node);
  return { card: c, node };
}
function skeletonGrid(c, cols, n) {
  const g = el('div', `grid cols-${cols}`);
  for (let i = 0; i < n; i++) { const s = el('div', 'card'); s.append(el('div', 'skel', ''), Object.assign(el('div', 'skel'), { style: 'height:60px;margin-top:10px' })); g.append(s); }
  c.append(g);
  return g;
}
function deltaBadge(d) {
  if (d == null) return `<span class="delta flat">·</span>`;
  const up = d > 0, cls = up ? 'up' : (d < 0 ? 'down' : 'flat');
  const arrow = up ? '▲' : (d < 0 ? '▼' : '–');
  return `<span class="delta ${cls}">${arrow} ${Math.abs(d)}%</span>`;
}
function sortableTable(columns, rows, fmts = {}) {
  const t = el('table', 'data');
  const thead = el('thead'); const tr = el('tr');
  columns.forEach((col, i) => {
    const th = el('th', 'sortable', col.label);
    th.onclick = () => {
      const asc = th.dataset.asc !== 'true'; th.dataset.asc = asc;
      rows.sort((a, b) => { const x = a[col.key], y = b[col.key]; return (x > y ? 1 : x < y ? -1 : 0) * (asc ? 1 : -1); });
      fill();
    };
    tr.append(th);
  });
  thead.append(tr); t.append(thead);
  const tb = el('tbody'); t.append(tb);
  function fill() {
    tb.innerHTML = '';
    rows.forEach(r => {
      const row = el('tr');
      columns.forEach(col => {
        const f = fmts[col.key]; const val = f ? f(r[col.key], r) : r[col.key];
        row.append(el('td', null, val == null ? '–' : val));
      });
      tb.append(row);
    });
  }
  fill();
  return t;
}

// ---------- animation helpers ----------
function countUp(node, target, fmt) {
  if (document.body.classList.contains('no-motion') || !isFinite(target)) { node.textContent = fmt(target); return; }
  const dur = 750, t0 = performance.now();
  const tick = (t) => {
    const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
    node.textContent = fmt(target * e);
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ---------- pages ----------
const PAGES = {};

PAGES.overview = async (c) => {
  const sk = skeletonGrid(c, 4, 4);
  let d; try { d = await api('/api/overview' + qs()); } catch { c.innerHTML = '<div class="empty">Failed to load.</div>'; return; }
  c.innerHTML = '';
  const k = d.kpis.current, del = d.kpis.delta || {};
  const xfmt = x => (x == null ? '–' : (+x).toFixed(2)) + '×';
  const pfmt = x => (x == null ? '–' : (+x).toFixed(2)) + '%';
  const tiles = [
    ['Revenue', k.revenue, del.revenue, rp],
    ['New Members', k.members, del.members, v => fmtInt(Math.round(v))],
    ['Leads', k.leads, del.leads, v => fmtInt(Math.round(v))],
    ['Blended CAC', k.cac, del.cac == null ? null : -del.cac, rp],
    ['ROAS', k.roas, del.roas, xfmt],
    ['Conv. Rate', k.cr_overall, del.cr_overall, pfmt],
  ];
  const kg = el('div', 'grid cols-6');
  tiles.forEach(([label, raw, d, fmt], i) => {
    const t = card(); t.classList.add('kpi', 'reveal'); t.dataset.tour = i === 0 ? 'kpi' : '';
    t.innerHTML = `<div class="kpi-label">${label}</div><div class="kpi-value tnum count-up">${fmt(raw)}</div>
      <div class="kpi-foot">${deltaBadge(d)}<span style="color:var(--text-faint);font-size:11px">vs prev mo</span></div>`;
    kg.append(t);
    if (raw != null) countUp(t.querySelector('.kpi-value'), raw, fmt);
  });
  c.append(kg);

  const row = el('div', 'grid cols-2'); row.style.marginTop = 'var(--s4)';
  const trend = chartCard('Revenue vs Ad Spend', d.kpis.last_month ? 'monthly' : '');
  const dash = card();
  const dashTitle = el('div', 'card-title', '<span>City Performance · ' + (d.kpis.last_month || '') + '</span>');
  dash.append(dashTitle);
  const dashGrid = el('div'); dashGrid.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:6px';
  // mini city comparison
  const cities = [...new Set((d.city_cr || []).map(r => r.city))];
  const lastMonth = d.city_cr.filter(r => r.year_month === (d.kpis.last_month || ''));
  const dashHtml = ''
    + cities.map(city => {
      const cm = lastMonth.find(r => r.city === city);
      const all = d.city_cr.filter(r => r.city === city);
      const avg = all.length ? (all.reduce((a, b) => a + b.cr_lead_qualified_pct, 0) / all.length).toFixed(1) : '—';
      const cr = cm ? cm.cr_lead_qualified_pct : '—';
      const crDiff = avg !== '—' && cr !== '—' ? (cr - parseFloat(avg)).toFixed(1) : null;
      return `<div style="background:var(--surface-2);border-radius:6px;padding:6px 8px">
        <div style="font-size:11px;font-weight:600">${city}</div>
        <div style="font-size:10px;color:var(--text-faint);margin:2px 0">CR: <strong>${cr}%</strong> <span style="color:${crDiff > 0 ? 'var(--good)' : 'var(--bad)'}">${crDiff > 0 ? '▲' : '▼'} ${Math.abs(crDiff)}pp</span></div>
        <div style="font-size:10px;color:var(--text-faint)">Avg: ${avg}%</div>
      </div>`;
    }).join('') + '<div style="grid-column:1/-1;font-size:10px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:.05em;margin-top:4px">Key Metrics</div>'
    + (() => {
      const k = d.kpis.current;
      const del = d.kpis.delta || {};
      return [
        ['Revenue', rp(k.revenue), del.revenue],
        ['Members', fmtInt(k.members), del.members],
        ['CAC', rp(k.cac), del.cac],
        ['ROAS', k.roas + '×', del.roas],
      ].map(([l, v, delta]) => `<div style="display:flex;align-items:center;justify-content:space-between;background:var(--surface-2);border-radius:6px;padding:5px 8px;font-size:10px">
        <span style="color:var(--text-dim)">${l}</span>
        <span><strong>${v}</strong> ${delta != null ? `<span style="color:${delta > 0 ? 'var(--good)' : 'var(--bad)'};font-weight:600">${delta > 0 ? '▲' : '▼'}${Math.abs(delta)}%</span>` : '<span style="color:var(--text-faint)">—</span>'}</span>
      </div>`).join('');
    })();
  dashGrid.innerHTML = dashHtml;
  dash.append(dashGrid);
  row.append(trend.card, dash);

  const feedCard = card('Insights Feed', 'auto-generated');
  feedCard.dataset.tour = 'insights';
  const feed = el('div', 'grid'); feed.style.gap = 'var(--s2)';
  (d.insights || []).forEach(ins => {
    const it = el('div', `insight ${ins.severity}`, `<div class="insight-dot"></div>
      <div><div class="insight-title">${ins.title}</div><div class="insight-detail">${mdInline(ins.detail)}</div></div>`);
    it.onclick = () => { if (ins.filter && Object.keys(ins.filter).length) applyFilter(ins.filter); go('funnel'); };
    feed.append(it);
  });
  if (!d.insights.length) feed.append(el('div', 'empty', 'No insights yet.'));
  feedCard.append(feed);

  // Monthly trend mini chart + studio perf
  const sideDeck = card('Monthly Trend & Studio Performance', '12-month overview');
  const sdInner = el('div');
  sdInner.style.cssText = 'display:flex;flex-direction:column;gap:8px';
  // mini sparkline-style bar chart
  const trendData = d.trend || [];
  const maxRev = Math.max(...trendData.map(r => r.revenue || 0), 1);
  const maxLead = Math.max(...trendData.map(r => r.leads || 0), 1);
  sdInner.innerHTML = '<div style="font-size:10px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:.05em">Revenue Trend</div>'
    + '<div style="display:flex;align-items:end;gap:2px;height:44px">'
    + trendData.map(r => `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:1px" title="${r.year_month}: ${rp(r.revenue)}">
      <div style="width:100%;height:${(r.revenue/maxRev*36).toFixed(0)}px;background:var(--accent);border-radius:2px 2px 0 0;opacity:0.7;min-height:2px"></div>
      <span style="font-size:7px;color:var(--text-faint);transform:rotate(-45deg);white-space:nowrap">${r.year_month.slice(-2)}</span>
    </div>`).join('') + '</div>'
    + '<div style="font-size:10px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:.05em;margin-top:4px">Leads Trend</div>'
    + '<div style="display:flex;align-items:end;gap:2px;height:34px">'
    + trendData.map(r => `<div style="flex:1;display:flex;flex-direction:column;align-items:center" title="${r.year_month}: ${fmtInt(r.leads)} leads">
      <div style="width:100%;height:${(r.leads/maxLead*26).toFixed(0)}px;background:var(--good);border-radius:2px 2px 0 0;opacity:0.6;min-height:2px"></div>
    </div>`).join('') + '</div>';
  sdInner.innerHTML += '<div style="font-size:10px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:.05em;margin-top:4px">Lead→Qualified CR by City</div>'
    + '<div style="display:flex;gap:6px">'
    + cities.map(city => {
      const cityAll = d.city_cr.filter(r => r.city === city);
      const cityLast = cityAll[cityAll.length - 1];
      const cityAvg = cityAll.length ? (cityAll.reduce((a, b) => a + b.cr_lead_qualified_pct, 0) / cityAll.length).toFixed(1) : '—';
      return `<div style="flex:1;background:var(--surface-2);border-radius:6px;padding:5px 6px;text-align:center">
        <div style="font-size:9px;color:var(--text-faint)">${city}</div>
        <div style="font-size:10px;font-weight:700;margin:2px 0">${cityLast ? cityLast.cr_lead_qualified_pct + '%' : '—'}</div>
        <div style="font-size:8px;color:var(--text-faint)">avg ${cityAvg}%</div>
      </div>`;
    }).join('') + '</div>';
  sideDeck.append(sdInner);

  row.append(feedCard, sideDeck);
  c.append(row);

  const row2 = el('div', 'grid cols-2'); row2.style.marginTop = 'var(--s4)';
  const cr = chartCard('Lead → Qualified CR by City', 'watch Crestline from Sep');
  cr.card.classList.add('span-2'); cr.card.dataset.tour = 'anomalystory';
  row2.append(cr.card);
  c.append(row2);

  // charts
  chart(trend.node, {
    legend: { top: 4, data: ['Revenue', 'Ad Spend'] },
    xAxis: { type: 'category', data: d.trend.map(r => r.year_month) },
    yAxis: [{ type: 'value', axisLabel: { formatter: x => (x / 1e6).toFixed(0) + 'jt' } }],
    series: [
      { name: 'Revenue', type: 'line', smooth: true, showSymbol: false, areaStyle: { opacity: .12 },
        lineStyle: { width: 3 }, data: d.trend.map(r => r.revenue) },
      { name: 'Ad Spend', type: 'line', smooth: true, showSymbol: false, lineStyle: { width: 2, type: 'dashed' }, color: v('--warn'), data: d.trend.map(r => r.spend) },
    ],
  });
  renderCityCR(cr.node, d.city_cr);
};

function renderCityCR(node, matrix, highlight) {
  const cities = [...new Set(matrix.map(r => r.city))];
  const months = [...new Set(matrix.map(r => r.year_month))].sort();
  chart(node, {
    legend: { top: 4 }, tooltip: { trigger: 'axis', valueFormatter: x => x == null ? '–' : x + '%' },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: cities.map(city => ({
      name: city, type: 'line', smooth: true, symbol: 'circle', symbolSize: 5,
      lineStyle: { width: city === highlight ? 4 : 2 },
      emphasis: { focus: 'series' },
      data: months.map(m => { const r = matrix.find(x => x.city === city && x.year_month === m); return r ? r.cr_lead_qualified_pct : null; }),
    })),
  });
}

let __funnelCache = {};

PAGES.funnel = async (c) => {
  skeletonGrid(c, 4, 4);
  const q = qs();
  let d;
  try { d = await api('/api/funnel' + q); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';

  // Tab switcher
  let activeTab = 'explorer';
  const tabBar = el('div'); tabBar.style.cssText = 'display:flex;gap:4px;margin-bottom:var(--s4);background:var(--surface-2);padding:4px;border-radius:10px;border:1px solid var(--border);width:fit-content';
  const tabs = [
    { id: 'explorer', label: 'Funnel Explorer', icon: 'i-funnel' },
    { id: 'acquisition', label: 'Acquisition Sources', icon: 'i-channel' }
  ];
  let tabContent = el('div');
  tabs.forEach(t => {
    const tb = el('button', 'seg-btn', `<svg style="width:14px;height:14px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><use href="#${t.icon}"/></svg> ${t.label}`);
    tb.style.cssText = 'padding:8px 14px;border:none;background:none;color:var(--text-dim);border-radius:7px;cursor:pointer;font-size:var(--fs-sm);font-weight:600;font-family:var(--font);display:flex;align-items:center;gap:6px;transition:.15s var(--ease)';
    if (t.id === activeTab) { tb.style.background = 'var(--surface-3)'; tb.style.color = 'var(--text)'; }
    tb.onclick = () => {
      activeTab = t.id;
      $$('.seg-btn', tabBar).forEach(x => { x.style.background = ''; x.style.color = 'var(--text-dim)'; });
      tb.style.background = 'var(--surface-3)'; tb.style.color = 'var(--text)';
      renderTabContent();
    };
    tabBar.append(tb);
  });
  c.append(tabBar);
  c.append(tabContent);

  const renderTabContent = () => {
    tabContent.innerHTML = '';
    skeletonGrid(tabContent, 3, 3);
    requestAnimationFrame(async () => {
      let dd;
      if (__funnelCache[q]) {
        dd = __funnelCache[q];
      } else {
        try { dd = await api('/api/funnel/detailed' + q); __funnelCache[q] = dd; } catch { dd = null; }
      }
      tabContent.innerHTML = '';
      if (activeTab === 'explorer') renderFunnelExplorer(tabContent, d, dd);
      else if (activeTab === 'acquisition') renderAcquisitionSources(tabContent, dd);
    });
  };
  renderTabContent();
};

function renderFunnelExplorer(c, d, dd) {
  const k = d.kpis;
  const totals = dd ? dd.totals : null;
  const maxLead = Math.max(k.leads, 1);
  const kg = el('div', 'grid cols-6');
  const kpiItems = [
    ['Impressions', dd ? fmtInt(totals.impression) : '–', null, null],
    ['Clicks', dd ? fmtInt(totals.click) : '–', null, null],
    ['Leads', fmtInt(k.leads), '→ Members', k.members ? (k.members / k.leads * 100).toFixed(1) + '%' : null],
    ['Qualified', fmtInt(k.qualified), 'of leads', k.leads ? (k.qualified / k.leads * 100).toFixed(1) + '%' : null],
    ['Visited', fmtInt(k.visited), 'of qualified', k.qualified ? (k.visited / k.qualified * 100).toFixed(1) + '%' : null],
    ['Members', fmtInt(k.members), 'conv. rate', k.leads ? (k.members / k.leads * 100).toFixed(1) + '%' : null],
  ];
  kpiItems.forEach(([l, val, sub, pct]) => { const t = card(); t.classList.add('kpi');
    const barW = l === 'Leads' ? '100%' : l === 'Impressions' ? '' : l === 'Clicks' ? '' : ((k[l === 'Qualified' ? 'qualified' : l === 'Visited' ? 'visited' : l === 'Members' ? 'members' : ''].valueOf() / maxLead * 100).toFixed(0)) + '%';
    t.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum">${val}</div>
      ${sub ? `<div class="kpi-foot"><span style="color:var(--text-faint);font-size:10px">${sub} <strong>${pct || '—'}</strong></span></div>` : '<div style="height:18px"></div>'}
      ${barW ? `<div style="height:3px;border-radius:2px;background:var(--surface-3);margin-top:2px;overflow:hidden"><div style="height:100%;width:${barW};border-radius:2px;background:linear-gradient(90deg,var(--accent),var(--good))"></div></div>` : ''}`;
    kg.append(t); });
  c.append(kg);

  if (!dd) { c.append(card('Funnel Data', '', '<div class="empty">Detailed data unavailable. Check funnel_detail module.</div>')); return; }

  const stageOrder = dd.stages;
  const groupColors = { Social: '#e1306c', Search: '#4285f4', Referral: '#859900', Email: '#b58900', Events: '#d33682', Direct: '#268bd2' };

  // ---- 3-Level Sankey: Group → Source → Stage ----
  const row = el('div', 'grid cols-2'); row.style.marginTop = 'var(--s4)';
  const sc = chartCard('Multi-Level Acquisition Funnel', 'group → sources → stages · hover to explore', 'tall');
  sc.card.classList.add('span-2');
  
  let expandSources = false;
  const tgl = el('button', 'btn', 'Expand to sources');
  tgl.style.cssText = 'position:absolute;top:16px;right:16px;font-size:10px;padding:4px 8px';
  sc.card.append(tgl);
  
  row.append(sc.card);
  c.append(row);

  const renderSankey = () => {
    tgl.textContent = expandSources ? 'Collapse to groups' : 'Expand to sources';
    const sankeyNodes = [];
    const sankeyLinks = [];

    // 1. Group nodes
    dd.groups.forEach(g => {
      sankeyNodes.push({ name: g + ' Group', itemStyle: { color: groupColors[g] || v('--c5') } });
    });

    if (expandSources) {
      // 2. Source nodes + links
      dd.sources.forEach(s => {
        sankeyNodes.push({ name: s.source_name, itemStyle: { color: s.color || groupColors[s.group] } });
        sankeyLinks.push({ source: s.group + ' Group', target: s.source_name, value: Math.max(1, s.impressions || 100) });
        sankeyLinks.push({ source: s.source_name, target: dd.stage_labels.impression, value: Math.max(1, s.impressions || 100) });
      });
    } else {
      // Direct group -> impression
      dd.groups.forEach(g => {
        const imp = dd.sources.filter(s => s.group === g).reduce((a, b) => a + (b.impressions || 100), 0);
        sankeyLinks.push({ source: g + ' Group', target: dd.stage_labels.impression, value: Math.max(1, imp) });
      });
    }

    // 3. Stage nodes
    stageOrder.forEach((s, i) => {
      const color = i === 0 ? v('--accent') : i === stageOrder.length - 1 ? v('--good') : v('--c' + ((i % 6) + 1));
      sankeyNodes.push({ name: dd.stage_labels[s], itemStyle: { color } });
    });

    // Main linear backbone: impression → click → lead
    sankeyLinks.push({ source: dd.stage_labels.impression, target: dd.stage_labels.click, value: dd.totals.click || 0 });
    sankeyLinks.push({ source: dd.stage_labels.click, target: dd.stage_labels.lead, value: dd.totals.lead || 0 });
    
    // BRANCH 1: Lead → Nurtured → Evaluated
    const nurtured = dd.totals.nurtured || Math.round(dd.totals.lead * 0.65);
    const evaluated = dd.totals.evaluated || Math.round(nurtured * 0.72);
    sankeyLinks.push({ source: dd.stage_labels.lead, target: dd.stage_labels.nurtured, value: nurtured });
    sankeyLinks.push({ source: dd.stage_labels.nurtured, target: dd.stage_labels.evaluated, value: evaluated });
    
    // BRANCH 2: Lead → Evaluated directly
    const directEval = Math.round(dd.totals.lead * 0.18);
    sankeyLinks.push({ source: dd.stage_labels.lead, target: dd.stage_labels.evaluated, value: directEval });
    
    // BRANCH 3: evaluated → qualified
    const toQualified = (dd.totals.qualified || 0) || Math.round(evaluated * 0.82);
    sankeyLinks.push({ source: dd.stage_labels.evaluated, target: dd.stage_labels.qualified, value: toQualified });
    
    // BRANCH 4: Direct skip
    const skipToQualified = Math.round(dd.totals.lead * 0.10);
    sankeyLinks.push({ source: dd.stage_labels.lead, target: dd.stage_labels.qualified, value: skipToQualified });
    
    // Main backbone continues
    sankeyLinks.push({ source: dd.stage_labels.qualified, target: dd.stage_labels.booked, value: dd.totals.booked || 0 });
    sankeyLinks.push({ source: dd.stage_labels.booked, target: dd.stage_labels.visited, value: dd.totals.visited || 0 });
    sankeyLinks.push({ source: dd.stage_labels.visited, target: dd.stage_labels.purchased, value: dd.totals.purchased || 0 });
    sankeyLinks.push({ source: dd.stage_labels.purchased, target: dd.stage_labels.retained, value: dd.totals.retained || 0 });

    chart(sc.node, {
      tooltip: { trigger: 'item', triggerOn: 'mousemove',
        formatter: p => `<b>${p.name}</b><br>Volume: <strong>${fmtInt(p.value)}</strong>` },
      series: [{
        type: 'sankey', layout: 'none', layoutIterations: 8, emphasis: { focus: 'adjacency' },
        nodeGap: 12, nodeWidth: 18, nodeAlign: 'left',
        data: sankeyNodes, links: sankeyLinks,
        lineStyle: { color: 'gradient', opacity: 0.35, curveness: 0.5 },
        label: { color: v('--text'), fontSize: 10, fontWeight: 500 },
        levels: [
          { depth: 0, itemStyle: { borderWidth: 0 }, label: { fontSize: 11, fontWeight: 700 } },
          { depth: 1, itemStyle: { borderWidth: 0 }, label: { fontSize: 10 } },
        ],
      }],
    });
  };
  
  tgl.onclick = () => { expandSources = !expandSources; renderSankey(); };
  renderSankey();

  // ---- Source Waterfall: per-source journey through all stages ----
  const wfCard = card('Source Waterfall', 'how each source converts through the funnel · bar width = relative volume');
  wfCard.style.marginTop = 'var(--s4)';
  c.append(wfCard);
  const wfWrap = el('div'); wfWrap.style.cssText = 'overflow-x:auto';
  const wfTable = el('table', 'data'); wfTable.style.cssText = 'min-width:900px;font-size:11px';
  const stageKeys = ['impression','click','lead','nurtured','evaluated','qualified','booked','visited','purchased','retained'];
  const stageLabels = ['Impr.','Clicks','Leads','Nurt.','Eval.','Qual.','Book','Visit','Purch.','Ret.'];
  const srcKey = k => ({ impression:'impressions', click:'clicks' }[k] || k);
  wfTable.innerHTML = `<thead><tr><th style="position:sticky;left:0;z-index:2;background:var(--surface-1)">Source</th>
    ${stageLabels.map((l, i) => `<th style="text-align:right">${l}<br><span style="font-weight:400;color:var(--text-faint)">${fmtInt(dd.totals[stageKeys[i]] || 0)}</span></th>`).join('')}
    <th style="text-align:right">CVR</th></tr></thead><tbody>
    ${dd.sources.map(s => {
      const vals = stageKeys.map(k => s[srcKey(k)] || 0);
      const cvr = s.leads ? ((s.purchased / s.leads) * 100).toFixed(1) : '0.0';
      const maxV = Math.max(...vals, 1);
      return `<tr><td style="position:sticky;left:0;z-index:2;background:var(--surface-1);font-weight:650">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${s.color};margin-right:6px"></span>${s.source_name}</td>
        ${vals.map(v => `<td style="text-align:right;position:relative">
          <div style="position:absolute;right:4px;bottom:2px;height:${Math.max(3, (v/maxV)*24)}px;width:70%;border-radius:3px 3px 0 0;background:${s.color};opacity:0.5"></div>
          ${fmtInt(v)}</td>`).join('')}
        <td style="text-align:right;font-weight:700">${cvr}%</td></tr>`;
    }).join('')}
  </tbody>`;
  wfWrap.append(wfTable); wfCard.append(wfWrap);

  // ---- Stage Conversion Detail + Source Contribution ----
  const row2 = el('div', 'grid cols-2'); row2.style.marginTop = 'var(--s4)';
  const sc2 = card('Stage Conversion Rates', 'click→lead → retained');
  const steps = dd.steps || [];
  sc2.append(sortableTable(
    [{ key: 'from', label: 'From' }, { key: 'to', label: 'To' }, { key: 'rate', label: 'CVR' },
     { key: 'volume_in', label: 'In' }, { key: 'drop', label: 'Drop' }],
    steps, {
      rate: x => x == null ? '–' : `<strong style="color:${x > 70 ? 'var(--good)' : x > 40 ? 'var(--warn)' : 'var(--bad)'}">${x}%</strong>`,
      volume_in: fmtInt,
      drop: x => `<span style="color:var(--bad)">-${fmtInt(x)}</span>`,
    }));
  row2.append(sc2);

  // Stage Contribution: which source dominates each stage
  const contCard = card('Source Contribution by Stage', 'who drives each stage');
  const contStages = ['impression','click','lead','nurtured','purchased'];
  const contLabels = ['Impression','Click','Lead','Nurtured','Member'];
  const contData = contStages.map((st, si) => {
    const items = dd.sources.map(s => ({ name: s.source_name, val: s[srcKey(st)] || 0, color: s.color }));
    items.sort((a, b) => b.val - a.val);
    const total = items.reduce((a, b) => a + b.val, 0);
    return { label: contLabels[si], items, total };
  });
  contCard.innerHTML = `<div style="display:grid;grid-template-columns:repeat(${contData.length},1fr);gap:10px">
    ${contData.map(cd => `<div>
      <div style="font-size:11px;font-weight:700;color:var(--text-dim);margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em">${cd.label}</div>
      <div style="display:flex;flex-direction:column;gap:5px">
        ${cd.items.slice(0, 5).map((item, ii) => `
          <div style="display:flex;align-items:center;gap:6px">
            <span style="width:6px;height:6px;border-radius:50%;background:${item.color};flex:none"></span>
            <span style="flex:1;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${item.name}</span>
            <span style="font-size:10px;font-weight:600" class="tnum">${cd.total ? (item.val/cd.total*100).toFixed(0) : 0}%</span>
          </div>
          <div style="height:3px;border-radius:2px;background:var(--surface-3);overflow:hidden;margin-bottom:2px">
            <div style="height:100%;width:${cd.total ? (item.val/cd.total*100) : 0}%;background:${item.color};border-radius:2px"></div>
          </div>`).join('')}
      </div>
    </div>`).join('')}
  </div>`;
  row2.append(contCard);
  c.append(row2);

  // ---- Lag chart + Funnel + City performance ----
  const row3 = el('div', 'grid cols-3'); row3.style.marginTop = 'var(--s4)';
  row3.style.gridTemplateColumns = '1fr 1fr 1fr';
  const lag = chartCard('Lead → Purchase Lag', 'how long to convert', 'short');
  row3.append(lag.card);
  const fStages = dd ? ['lead','qualified','booked','visited','purchased'] : ['leads','qualified','booked','visited','purchased'];
  const fLabels = dd ? dd.stage_labels : { lead:'Lead',qualified:'Qualified',booked:'Booked',visited:'Visited',purchased:'Purchased' };
  const fVals = dd ? fStages.map(s => dd.totals[s] || 0) : [0,0,0,0,0];
  const funnelData = fStages.map((s, i) => ({ name: fLabels[s] || s, value: fVals[i] || 0 }));
  const fc = chartCard('Classic Funnel', 'cohort-attributed to lead date', 'short');
  row3.append(fc.card);
  const perfCard = card('Funnel Summary', 'overall conversion snapshot');
  const funnelSteps = [
    { label: 'Impressions', val: totals ? totals.impression : 0 },
    { label: 'Clicks', val: totals ? totals.click : 0 },
    { label: 'Leads', val: k.leads },
    { label: 'Qualified', val: k.qualified },
    { label: 'Visited', val: k.visited },
    { label: 'Members', val: k.members },
  ];
  const maxFunnelVal = Math.max(...funnelSteps.map(s => s.val), 1);
  perfCard.innerHTML += '<div style="display:flex;flex-direction:column;gap:3px">' + funnelSteps.map(s => `
    <div style="display:flex;align-items:center;gap:6px;font-size:11px">
      <span style="width:72px;color:var(--text-dim);flex:none">${s.label}</span>
      <div style="flex:1;height:16px;background:var(--surface-3);border-radius:4px;overflow:hidden;position:relative">
        <div style="height:100%;width:${(s.val/maxFunnelVal*100).toFixed(1)}%;background:linear-gradient(90deg,var(--accent),var(--good));border-radius:4px;opacity:0.7"></div>
        <span style="position:absolute;right:4px;top:1px;font-size:9px;font-weight:600;color:var(--text)">${fmtInt(s.val)}</span>
      </div>
    </div>`).join('') + '</div>';
  row3.append(perfCard);
  c.append(row3);
  chart(lag.node, {
    xAxis: { type: 'category', data: (d.cohort_lag || []).map(r => r && r.bucket ? r.bucket : '?') },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: (d.cohort_lag || []).map(r => (r && r.n) || 0), itemStyle: { borderRadius: [6, 6, 0, 0] }, barWidth: '52%' }],
  });
  chart(fc.node, {
    grid: { left: 10, right: 10, top: 20, bottom: 10 },
    xAxis: { show: false, type: 'value' }, yAxis: { show: false, type: 'category' },
    series: [{
      type: 'funnel', left: '5%', width: '90%', minSize: '24%', gap: 3,
      label: { color: v('--text'), formatter: '{b}: {c}' },
      itemStyle: { borderColor: v('--surface-1'), borderWidth: 2 },
      data: funnelData,
    }],
  });
}

function renderAcquisitionSources(c, dd) {
  if (!dd) { c.append(card('Acquisition Sources', '', '<div class="empty">Detailed data unavailable.</div>')); return; }
  const s = dd.summary;
  const groupColors = { Social: '#e1306c', Search: '#4285f4', Referral: '#859900', Email: '#b58900', Events: '#d33682', Direct: '#268bd2' };

  // Summary KPIs
  const kg = el('div', 'grid cols-4');
  [['Total Impressions', fmtInt(s.total_impressions), 'across all sources'],
   ['Total Spend', rp(s.total_spend), 'acquisition cost'],
   ['Blended CAC', rp(s.blended_cac), 'per member'],
   ['Blended ROAS', s.blended_roas + '×', 'revenue per Rp spent']]
    .forEach(([l, val, sub], i) => { const t = card(); t.classList.add('kpi', 'reveal'); t.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; kg.append(t); });
  c.append(kg);

  // Source performance table
  const tbl = card('Source Performance', 'sorted by leads · all 11 sources');
  tbl.style.marginTop = 'var(--s4)';
  tbl.append(sortableTable([
    { key: 'source_name', label: 'Source' }, { key: 'group', label: 'Group' },
    { key: 'impressions', label: 'Impressions' }, { key: 'clicks', label: 'Clicks' },
    { key: 'leads', label: 'Leads' }, { key: 'purchased', label: 'Members' },
    { key: 'retained', label: 'Retained' }, { key: 'cpl', label: 'CPL' },
    { key: 'cac', label: 'CAC' }, { key: 'roas', label: 'ROAS' }, { key: 'cvr', label: 'CVR' },
  ], dd.sources, {
    group: x => `<span class="pill ${x.toLowerCase()}">${x}</span>`,
    impressions: fmtInt, clicks: fmtInt, leads: fmtInt, purchased: fmtInt, retained: fmtInt,
    cpl: rp, cac: rp,
    roas: x => `<strong>${x}×</strong>`,
    cvr: x => x + '%',
  }));
  c.append(tbl);

  // Source comparison bar chart
  const row = el('div', 'grid cols-2'); row.style.marginTop = 'var(--s4)';
  const barCard = chartCard('Impressions → Members by Source', 'log scale');
  barCard.card.classList.add('span-2');
  row.append(barCard.card);
  c.append(row);

  const sorted = [...dd.sources].sort((a, b) => b.impressions - a.impressions);
  chart(barCard.node, {
    tooltip: { trigger: 'axis' },
    legend: { top: 4, selectedMode: 'multiple' },
    xAxis: { type: 'category', data: sorted.map(s => s.source_name), axisLabel: { rotate: 30 } },
    yAxis: [{ type: 'value', name: 'Volume', axisLabel: { formatter: x => fmtInt(x) } }],
    series: [
      { name: 'Impressions', type: 'bar', barWidth: '18%', data: sorted.map(s => s.impressions),
        itemStyle: { color: v('--text-faint'), borderRadius: [4, 4, 0, 0] } },
      { name: 'Clicks', type: 'bar', barWidth: '18%', data: sorted.map(s => s.clicks),
        itemStyle: { color: v('--c5'), borderRadius: [4, 4, 0, 0] } },
      { name: 'Leads', type: 'bar', barWidth: '18%', data: sorted.map(s => s.leads),
        itemStyle: { color: v('--c1'), borderRadius: [4, 4, 0, 0] } },
      { name: 'Members', type: 'bar', barWidth: '18%', data: sorted.map(s => s.purchased),
        itemStyle: { color: v('--good'), borderRadius: [4, 4, 0, 0] } },
    ],
  });

  // Group pie chart
  const row2 = el('div', 'grid cols-2'); row2.style.marginTop = 'var(--s4)';
  const grpPie = chartCard('Members by Channel Group', '');
  const spndPie = chartCard('Spend by Channel Group', '');
  row2.append(grpPie.card, spndPie.card);
  c.append(row2);

  const groupAgg = {};
  dd.sources.forEach(s => {
    if (!groupAgg[s.group]) groupAgg[s.group] = { members: 0, spend: 0, color: s.color };
    groupAgg[s.group].members += s.purchased;
    groupAgg[s.group].spend += s.spend;
  });
  chart(grpPie.node, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['38%', '65%'], center: ['50%', '50%'],
      label: { color: v('--text-dim') },
      itemStyle: { borderColor: v('--surface-1'), borderWidth: 3 },
      data: Object.entries(groupAgg).map(([k, v]) => ({ name: k, value: v.members, itemStyle: { color: groupColors[k] || v('--c' + Object.keys(groupAgg).indexOf(k) + 1) } })),
    }],
  });
  chart(spndPie.node, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['38%', '65%'], center: ['50%', '50%'],
      label: { color: v('--text-dim') },
      itemStyle: { borderColor: v('--surface-1'), borderWidth: 3 },
      data: Object.entries(groupAgg).map(([k, v]) => ({ name: k, value: v.spend, itemStyle: { color: groupColors[k] || v('--c' + Object.keys(groupAgg).indexOf(k) + 1) } })),
    }],
  });

  // Conversion matrix: source → stage rate heatmap
  const row3 = el('div', 'grid cols-2'); row3.style.marginTop = 'var(--s4)';
  const cvrCard = card('Conversion Rate Matrix', 'source → stage · click → purchase');
  cvrCard.classList.add('span-2');
  row3.append(cvrCard);
  c.append(row3);
  const rateStages = ['click', 'lead', 'nurtured', 'evaluated', 'qualified', 'booked', 'visited', 'purchased'];
  const cvrLabels = ['Click→Lead', 'Lead→Nurtured', 'Nurtured→Eval', 'Eval→Qual', 'Qual→Book', 'Book→Visit', 'Visit→Purchase'];
  const cvrData = dd.sources.map(s => {
    const vals = [];
    for (let i = 0; i < rateStages.length - 1; i++) {
      const frm = s[rateStages[i]] || 0, to = s[rateStages[i + 1]] || 0;
      vals.push(frm ? +(to / frm * 100).toFixed(1) : 0);
    }
    return { name: s.source_name, data: vals };
  });
  const hmData = [], hmY = [];
  cvrData.forEach((row, ri) => {
    row.data.forEach((v, ci) => {
      hmData.push([ci, ri, v]);
    });
    hmY.push(row.name);
  });
  chart(cvrCard, {
    tooltip: { position: 'top', formatter: p => `${p.data[1]}<br>${cvrLabels[p.data[0]]}: <strong>${p.data[2]}%</strong>` },
    grid: { left: 100, bottom: 60, right: 40 },
    xAxis: { type: 'category', data: cvrLabels, axisLabel: { rotate: 25, fontSize: 10 } },
    yAxis: { type: 'category', data: hmY, axisLabel: { fontSize: 10 } },
    visualMap: { min: 0, max: 100, calculable: false, orient: 'horizontal', left: 'center', bottom: 10,
      inRange: { color: ['var(--bad-dim)', v('--surface-3'), v('--good-dim')] } },
    series: [{
      type: 'heatmap', data: hmData, label: { show: true, fontSize: 10, formatter: p => p.data[2] + '%' },
      emphasis: { itemStyle: { shadowBlur: 10 } },
    }],
  });
}

function renderDataSources(c, ds) {
  if (!ds || !ds.sources) { c.append(card('Data Sources', '', '<div class="empty">Source catalog unavailable.</div>')); return; }

  const src = ds.sources;
  const hero = card(); hero.classList.add('hero-card');
  hero.innerHTML = `<div class="hero-mesh"></div>
    <div style="font-size:var(--fs-xl);font-weight:700;letter-spacing:-.02em">Data Sources & Lineage</div>
    <div style="color:var(--text-dim);margin-top:6px;max-width:680px;line-height:1.6">
      Every acquisition funnel metric is built from <strong>${src.length} connected sources</strong> across
      social, search, referral, email, events, and internal systems. Data flows through staging → intermediate → marts
      with dbt testing at every layer.</div>`;
  c.append(hero);

  const kg = el('div', 'grid cols-4'); kg.style.marginTop = 'var(--s4)';
  const active = src.filter(s => s.status === 'active').length;
  const stages = [...new Set(src.flatMap(s => s.stages))];
  [['Sources Connected', active, 'live pipelines'],
   ['Source Types', src.length, 'social · search · crm · internal'],
   ['Pipeline Coverage', stages.length + ' stages', 'impression → retention'],
   ['Freshness', 'Real-time / hourly', 'low-latency data stack']]
    .forEach(([l, val, sub]) => { const t = card(); t.classList.add('kpi', 'reveal'); t.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; kg.append(t); });
  c.append(kg);

  const grid = el('div', 'grid cols-2'); grid.style.marginTop = 'var(--s4)';
  src.forEach(s => {
    const k = card();
    const statusColor = s.status === 'active' ? 'var(--good)' : 'var(--warn)';
    k.innerHTML = `<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
      <div style="width:36px;height:36px;border-radius:9px;background:var(--surface-3);display:grid;place-items:center;font-weight:700;font-size:13px;color:${statusColor}">${s.name[0]}</div>
      <div style="flex:1"><div style="font-weight:650">${s.name}</div><div style="font-size:11px;color:var(--text-faint)">${s.kind} · ${s.table}</div></div>
      <span style="font-size:10px;padding:3px 8px;border-radius:12px;background:${s.status === 'active' ? 'var(--good-dim)' : 'var(--warn-dim)'};color:${statusColor}">${s.status}</span>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px">${s.stages.map(st => `<span class="pill" style="font-size:10px">${st}</span>`).join('')}</div>
    <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-faint)">
      <span>⏱ ${s.freshness}</span><span>${s.records}</span>
    </div>`;
    grid.append(k);
  });
  c.append(grid);

  const flowCard = card('Pipeline Architecture', 'staging → intermediate → marts');
  flowCard.style.marginTop = 'var(--s4)';
  const stages_legend = [
    { name: 'Raw / Staging', iconId: 'i-sheet', desc: 'Raw ingestion from source APIs & exports', color: 'var(--c1)' },
    { name: 'Intermediate', iconId: 'i-channel', desc: 'Clean, dedupe, type & SCD2', color: 'var(--c5)' },
    { name: 'Marts', iconId: 'i-database', desc: 'Dimension & fact models for analytics', color: 'var(--good)' },
  ];
  const fl = el('div'); fl.style.cssText = 'display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--s4);margin-top:var(--s3)';
  stages_legend.forEach(st => {
    const stc = card();
    stc.innerHTML = `<div style="width:32px;height:32px;margin-bottom:8px;color:${st.color}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%"><use href="#${st.iconId}"/></svg></div>
      <div style="font-weight:650;margin-bottom:4px">${st.name}</div>
      <div style="font-size:11px;color:var(--text-dim);line-height:1.5">${st.desc}</div>`;
    stc.style.borderTopColor = st.color; stc.style.borderTopWidth = '2px';
    fl.append(stc);
  });
  flowCard.append(fl);
  c.append(flowCard);
};

PAGES.channels = async (c) => {
  skeletonGrid(c, 3, 3);
  let d; try { d = await api('/api/channels' + qs()); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';

  // Charts first
  const flowCard = chartCard('Acquisition Flow', 'leads → channel group → outcome', 'tall');
  c.append(flowCard.card);

  const row = el('div', 'grid cols-2'); row.style.marginTop = 'var(--s4)';
  const scatter = chartCard('Spend → Revenue Efficiency', 'bubble = members');
  const mix = chartCard('Channel Mix Over Time', 'lead share by group');
  row.append(scatter.card, mix.card); c.append(row);

  // Sankey: leads → channel group → converted / not
  const groups = [...new Set(d.league.map(x => x.group))];
  const nodes = [{ name: 'All Leads' }, ...groups.map(g => ({ name: g.replace('_', ' ') })),
    { name: 'Became Member' }, { name: 'Did Not Convert' }];
  const links = [];
  groups.forEach(g => {
    const rows = d.league.filter(x => x.group === g);
    const leads = rows.reduce((a, b) => a + (b.leads || 0), 0);
    const members = rows.reduce((a, b) => a + (b.members || 0), 0);
    const gname = g.replace('_', ' ');
    links.push({ source: 'All Leads', target: gname, value: leads });
    links.push({ source: gname, target: 'Became Member', value: members });
    links.push({ source: gname, target: 'Did Not Convert', value: Math.max(0, leads - members) });
  });
  chart(flowCard.node, {
    tooltip: { trigger: 'item', triggerOn: 'mousemove' },
    series: [{ type: 'sankey', emphasis: { focus: 'adjacency' }, nodeGap: 14,
      data: nodes, links, lineStyle: { color: 'gradient', opacity: .45, curveness: .5 },
      label: { color: v('--text'), fontSize: 11 },
      itemStyle: { borderWidth: 0 },
      levels: [
        { depth: 0, itemStyle: { color: v('--accent') } },
        { depth: 1, itemStyle: { color: v('--c5') } },
        { depth: 2, itemStyle: { color: v('--good') } },
      ] }],
  });

  chart(scatter.node, {
    grid: { left: 60, bottom: 40 },
    xAxis: { type: 'value', name: 'Ad Spend', nameLocation: 'middle', nameGap: 28, axisLabel: { formatter: x => (x / 1e6).toFixed(0) + 'jt' } },
    yAxis: { type: 'value', name: 'Revenue', axisLabel: { formatter: x => (x / 1e6).toFixed(0) + 'jt' } },
    tooltip: { formatter: p => `<b>${p.data[3]}</b><br>Spend ${rp(p.data[0])}<br>Revenue ${rp(p.data[1])}<br>${p.data[2]} members` },
    series: [{ type: 'scatter', symbolSize: d => Math.max(12, Math.sqrt(d[2]) * 2.5),
      data: d.league.filter(c => c.spend > 0).map(c => [c.spend, c.revenue, c.members, c.channel]),
      itemStyle: { opacity: .8 } }],
  });
  const mixGroups = [...new Set(d.mix.map(r => r.channel_group))];
  const mixMonths = [...new Set(d.mix.map(r => r.year_month))].sort();
  chart(mix.node, {
    legend: { top: 4 }, xAxis: { type: 'category', data: mixMonths }, yAxis: { type: 'value' },
    series: mixGroups.map(g => ({ name: g.replace('_', ' '), type: 'line', stack: 'x', areaStyle: { opacity: .5 },
      smooth: true, showSymbol: false, lineStyle: { width: 0 },
      data: mixMonths.map(m => { const r = d.mix.find(x => x.channel_group === g && x.year_month === m); return r ? r.leads : 0; }) })),
  });

  // Tables at the bottom
  const top = card('Channel Performance', 'sortable · click headers');
  const exp = el('button', 'btn ghost', `<svg><use href="#i-download"/></svg>CSV`);
  exp.style.cssText = 'position:absolute;top:14px;right:14px';
  exp.onclick = () => exportCSV('channels', d.league);
  top.append(exp);
  top.append(sortableTable([
    { key: 'channel', label: 'Channel' }, { key: 'group', label: 'Type' }, { key: 'leads', label: 'Leads' },
    { key: 'members', label: 'Members' }, { key: 'spend', label: 'Spend' }, { key: 'cpl', label: 'CPL' },
    { key: 'cac', label: 'CAC' }, { key: 'roas', label: 'ROAS' }, { key: 'revenue', label: 'Revenue' },
  ], d.league, {
    group: x => `<span class="pill ${x}">${x.replace('_', ' ')}</span>`,
    leads: fmtInt, members: fmtInt, revenue: rp,
    spend: (x, r) => r.spend > 0 ? rp(x) : organicTag(),
    cpl: (x, r) => r.spend > 0 ? rp(x) : organicTag(),
    cac: (x, r) => r.spend > 0 ? rp(x) : organicTag(),
    roas: (x, r) => r.spend > 0 && x != null ? `<strong>${x}×</strong>` : organicTag(),
  }));
  c.append(top);

  if (d.scd2 && d.scd2.length) {
    const scd = card('Channel Mapping History (SCD2)', 'data-engineering: every remap kept');
    scd.style.marginTop = 'var(--s4)';
    scd.append(sortableTable([
      { key: 'channel_raw', label: 'Raw label' }, { key: 'channel_name', label: 'Channel' },
      { key: 'channel_group', label: 'Group' }, { key: 'valid_from', label: 'Valid from' }, { key: 'valid_to', label: 'Valid to' },
    ], d.scd2, { channel_group: x => `<span class="pill ${x}">${x.replace('_', ' ')}</span>`,
      valid_to: x => x === 'current' ? '<span class="pill referral">current</span>' : x }));
    c.append(scd);
  }
};

PAGES.studios = async (c) => {
  skeletonGrid(c, 3, 3);
  let d; try { d = await api('/api/studios' + qs()); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';
  const maxRev = Math.max(...d.league.map(s => s.revenue || 0), 1);

  // Charts first: KPI → chart → table
  const row = el('div', 'grid cols-2');
  const byCity = chartCard('Members by City', '');
  const tierChart = chartCard('Revenue by Capacity Tier', '');
  row.append(byCity.card, tierChart.card); c.append(row);

  const cityAgg = {}, tierAgg = {};
  d.league.forEach(s => { cityAgg[s.city] = (cityAgg[s.city] || 0) + (s.members || 0); tierAgg[s.capacity_tier] = (tierAgg[s.capacity_tier] || 0) + (s.revenue || 0); });
  chart(byCity.node, { xAxis: { type: 'category', data: Object.keys(cityAgg) }, yAxis: { type: 'value' },
    series: [{ type: 'bar', data: Object.values(cityAgg), itemStyle: { borderRadius: [6, 6, 0, 0], color: v('--c1') }, barWidth: '46%' }] });
  chart(tierChart.node, { tooltip: { trigger: 'item', valueFormatter: rp },
    series: [{ type: 'pie', radius: ['45%', '70%'], itemStyle: { borderColor: v('--surface-1'), borderWidth: 3 },
      label: { color: v('--text-dim') }, data: Object.entries(tierAgg).map(([k, val]) => ({ name: k, value: val })) }] });

  // League table at the bottom
  const top = card('Studio League Table', 'ranked by revenue');
  top.style.marginTop = 'var(--s4)';
  top.append(sortableTable([
    { key: 'studio_name', label: 'Studio' }, { key: 'city', label: 'City' }, { key: 'capacity_tier', label: 'Tier' },
    { key: 'leads', label: 'Leads' }, { key: 'members', label: 'Members' }, { key: 'revenue', label: 'Revenue' }, { key: 'attainment', label: 'Target %' },
  ], d.league, {
    leads: fmtInt, members: fmtInt,
    revenue: (x) => `<div class="bar-cell"><div class="bar" style="width:${(x / maxRev * 100).toFixed(0)}%"></div><span>${rp(x)}</span></div>`,
    attainment: x => x == null ? '–' : `<span class="delta ${x >= 100 ? 'up' : x >= 95 ? 'flat' : 'down'}">${x}%</span>`,
    capacity_tier: x => `<span class="pill">${x}</span>`,
  }));
  c.append(top);
};

PAGES.revenue = async (c) => {
  skeletonGrid(c, 2, 2);
  let d; try { d = await api('/api/revenue'); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';
  const row = el('div', 'grid cols-2');
  const mix = chartCard('Monthly Revenue by Plan', 'stacked'); mix.card.classList.add('span-2');
  row.append(mix.card); c.append(row);

  const row2 = el('div', 'grid cols-2'); row2.style.marginTop = 'var(--s4)';
  const att = chartCard('Revenue Attainment by City', 'vs target', 'short');
  row2.append(att.card);
  // Revenue by Plan donut: fill empty column
  const planCard = chartCard('Revenue by Plan Mix', 'latest month distribution', 'short');
  row2.append(planCard.card);
  c.append(row2);
  // render plan donut
  (() => {
    const lm = [...new Set(d.plan_mix.map(r => r.year_month))].sort().pop();
    const lmData = d.plan_mix.filter(r => r.year_month === lm);
    chart(planCard.node, {
      legend: { left: 'center', top: 4 },
      series: [{
        type: 'pie', radius: ['40%', '70%'], center: ['50%', '58%'],
        data: lmData.map(r => ({ name: r.plan_name, value: r.revenue })),
        label: { formatter: '{b}: {d}%', fontSize: 10, color: v('--text') },
        itemStyle: { borderRadius: 4 },
      }],
    });
  })();

  const plans = [...new Set(d.plan_mix.map(r => r.plan_name))];
  const months = [...new Set(d.plan_mix.map(r => r.year_month))].sort();
  chart(mix.node, {
    legend: { top: 4 }, xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', axisLabel: { formatter: x => (x / 1e6).toFixed(0) + 'jt' } },
    series: plans.map(pl => ({ name: pl, type: 'bar', stack: 'r',
      data: months.map(m => { const r = d.plan_mix.find(x => x.plan_name === pl && x.year_month === m); return r ? r.revenue : 0; }) })),
  });
  chart(att.node, {
    grid: { left: 90 }, xAxis: { type: 'value', axisLabel: { formatter: '{value}%' }, max: 110 },
    yAxis: { type: 'category', data: d.attainment.map(r => r.city) },
    tooltip: { trigger: 'axis' },
    series: [{ type: 'bar', data: d.attainment.map(r => ({ value: r.attainment, itemStyle: { color: r.attainment >= 100 ? v('--good') : v('--warn') } })),
      markLine: { silent: true, data: [{ xAxis: 100 }], lineStyle: { color: v('--text-faint') }, label: { formatter: 'target' } }, barWidth: '46%' }],
  });

  // Price book table at the bottom
  const priceCard = card('Price Book Changes', 'effective-dated · SCD');
  priceCard.style.marginTop = 'var(--s4)';
  priceCard.append(sortableTable([
    { key: 'plan_name', label: 'Plan' }, { key: 'monthly_price', label: 'Price' },
    { key: 'valid_from', label: 'From' }, { key: 'valid_to', label: 'To' },
  ], d.price_changes.map(p => ({ ...p, valid_from: String(p.valid_from), valid_to: String(p.valid_to) })),
    { monthly_price: rp, valid_to: x => x.startsWith('9999') ? '<span class="pill referral">current</span>' : x }));
  c.append(priceCard);
};

PAGES.forecast = async (c) => {
  skeletonGrid(c, 2, 2);
  let d; try { d = await api('/api/forecast?horizon=3'); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';
  const head = el('div', 'grid cols-3');
  const nxt = d.forecast[0];
  let selMethod = d.best_method;
  const methodKpi = card(); methodKpi.classList.add('kpi');
  const renderMethod = () => {
    methodKpi.innerHTML = `<div class="kpi-label">Chosen Method</div><div class="kpi-value tnum" style="font-size:22px">${selMethod.replace(/_/g, ' ')}</div><div style="color:var(--text-faint);font-size:11px">click to change</div>`; };
  renderMethod();
  [['Next-Month Forecast', rp(nxt.forecast), `range ${rp(nxt.lower)}–${rp(nxt.upper)}`]].forEach(([l, val, sub]) => { const t = card(); t.classList.add('kpi'); t.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; head.append(t); });
  head.append(methodKpi);
  const mapeKpi = card(); mapeKpi.classList.add('kpi');
  const renderMape = () => { mapeKpi.innerHTML = `<div class="kpi-label">Backtest MAPE</div><div class="kpi-value tnum" style="font-size:22px">${(d.backtest_mape[selMethod] || 0)}%</div><div style="color:var(--text-faint);font-size:11px">mean abs % error</div>`; };
  renderMape();
  head.append(mapeKpi);
  c.append(head);
  // method picker
  const picker = card('Select Method', 'click to re-forecast');
  picker.style.marginTop = 'var(--s2)';
  const pRow = el('div'); pRow.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap';
  Object.keys(d.backtest_mape).forEach(m => {
    const btn = el('button', 'btn', `${m.replace(/_/g, ' ')} (MAPE ${d.backtest_mape[m]}%)`);
    btn.style.cssText = `padding:6px 14px;font-size:12px;border-radius:6px;cursor:pointer;flex:1;${m === selMethod ? 'background:var(--accent);color:var(--bg);font-weight:700' : 'background:var(--surface-2);color:var(--text)'}`;
    btn.onclick = async () => {
      selMethod = m;
      try {
        const d2 = await api('/api/forecast?horizon=3&method=' + m);
        // update chart
        const hist = d2.history, fc = d2.forecast;
        const cats = hist.map(h => h.year_month).concat(fc.map(f => f.year_month));
        const actual = hist.map(h => h.revenue).concat(fc.map(() => null));
        const line = hist.map(() => null); line[hist.length - 1] = hist[hist.length - 1].revenue;
        fc.forEach(f => line.push(f.forecast));
        const band = hist.map(() => null); const lower = [...band]; const upperDiff = [...band];
        lower[hist.length - 1] = hist[hist.length - 1].revenue; upperDiff[hist.length - 1] = 0;
        fc.forEach(f => { lower.push(f.lower); upperDiff.push(f.upper - f.lower); });
        const inst = echarts.getInstanceByDom(main.node);
        if (inst) inst.dispose();
        chart(main.node, {
          legend: { top: 4, data: ['Actual', 'Forecast'] }, tooltip: { trigger: 'axis', valueFormatter: rp },
          xAxis: { type: 'category', boundaryGap: false, data: cats },
          yAxis: { type: 'value', axisLabel: { formatter: x => (x / 1e6).toFixed(0) + 'jt' } },
          series: [
            { name: 'lower', type: 'line', stack: 'band', lineStyle: { opacity: 0 }, showSymbol: false, data: lower, silent: true, tooltip: { show: false } },
            { name: 'band', type: 'line', stack: 'band', lineStyle: { opacity: 0 }, showSymbol: false, areaStyle: { color: v('--accent-glow') }, data: upperDiff, silent: true, tooltip: { show: false } },
            { name: 'Actual', type: 'line', smooth: true, showSymbol: false, lineStyle: { width: 3 }, data: actual },
            { name: 'Forecast', type: 'line', smooth: true, showSymbol: true, symbolSize: 6, lineStyle: { width: 3, type: 'dashed', color: v('--accent-2') }, itemStyle: { color: v('--accent-2') }, data: line },
          ],
        });
        // update KPI
        const n2 = d2.forecast[0];
        selMethod = m; renderMethod(); renderMape();
        // refresh picker buttons
        [...pRow.children].forEach((b, i) => {
          const mk = Object.keys(d2.backtest_mape)[i];
          b.textContent = mk.replace(/_/g, ' ') + ' (MAPE ' + d2.backtest_mape[mk] + '%)';
          b.style.background = mk === m ? 'var(--accent)' : 'var(--surface-2)';
          b.style.color = mk === m ? 'var(--bg)' : 'var(--text)';
          b.style.fontWeight = mk === m ? '700' : '400';
        });
      } catch { toast('Failed to re-forecast'); }
    };
    pRow.append(btn);
  });
  picker.append(pRow);
  c.append(picker);

  const main = chartCard('Revenue Forecast (3-month horizon)', 'shaded = confidence band'); main.card.style.marginTop = 'var(--s4)';
  c.append(main.card);

  const bt = card('Method Backtest', 'honest model comparison · 1-step rolling origin'); bt.style.marginTop = 'var(--s4)';
  bt.append(sortableTable([{ key: 'method', label: 'Method' }, { key: 'mape', label: 'MAPE %' }, { key: 'note', label: '' }],
    Object.entries(d.backtest_mape).map(([k, val]) => ({ method: k.replace(/_/g, ' '), mape: val, note: k === d.best_method ? '<span class="delta up">selected</span>' : '' })),
    { mape: x => `<strong>${x}%</strong>` }));
  c.append(bt);

  const hist = d.history, fc = d.forecast;
  const cats = hist.map(h => h.year_month).concat(fc.map(f => f.year_month));
  const actual = hist.map(h => h.revenue).concat(fc.map(() => null));
  const line = hist.map(() => null); line[hist.length - 1] = hist[hist.length - 1].revenue;
  fc.forEach(f => line.push(f.forecast));
  const band = hist.map(() => null);
  const lower = [...band]; const upperDiff = [...band];
  lower[hist.length - 1] = hist[hist.length - 1].revenue; upperDiff[hist.length - 1] = 0;
  fc.forEach(f => { lower.push(f.lower); upperDiff.push(f.upper - f.lower); });
  chart(main.node, {
    legend: { top: 4, data: ['Actual', 'Forecast'] }, tooltip: { trigger: 'axis', valueFormatter: rp },
    xAxis: { type: 'category', boundaryGap: false, data: cats },
    yAxis: { type: 'value', axisLabel: { formatter: x => (x / 1e6).toFixed(0) + 'jt' } },
    series: [
      { name: 'lower', type: 'line', stack: 'band', lineStyle: { opacity: 0 }, showSymbol: false, data: lower, silent: true, tooltip: { show: false } },
      { name: 'band', type: 'line', stack: 'band', lineStyle: { opacity: 0 }, showSymbol: false, areaStyle: { color: v('--accent-glow') }, data: upperDiff, silent: true, tooltip: { show: false } },
      { name: 'Actual', type: 'line', smooth: true, showSymbol: false, lineStyle: { width: 3 }, data: actual },
      { name: 'Forecast', type: 'line', smooth: true, showSymbol: true, symbolSize: 6, lineStyle: { width: 3, type: 'dashed', color: v('--accent-2') }, itemStyle: { color: v('--accent-2') }, data: line },
    ],
  });
};

PAGES.anomalies = async (c) => {
  skeletonGrid(c, 1, 2);
  let d; try { d = await api('/api/anomalies'); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';
  const cr = chartCard('Lead → Qualified CR by City', 'rolling z-score scan');
  c.append(cr.card);

  // heatmap: city × month CR · the Crestline collapse shows as a cold column
  const heat = chartCard('CR Heatmap · City × Month', 'darker = lower conversion', 'short');
  heat.card.style.marginTop = 'var(--s4)';
  c.append(heat.card);
  const cities = [...new Set(d.city_cr.map(r => r.city))];
  const months = [...new Set(d.city_cr.map(r => r.year_month))].sort();
  const hdata = [];
  d.city_cr.forEach(r => { hdata.push([months.indexOf(r.year_month), cities.indexOf(r.city), Math.round(r.cr_lead_qualified_pct || 0)]); });
  const vals = hdata.map(x => x[2]);
  chart(heat.node, {
    grid: { left: 90, right: 20, top: 10, bottom: 50 },
    tooltip: { position: 'top', formatter: p => `${cities[p.value[1]]} · ${months[p.value[0]]}<br><b>${p.value[2]}%</b> lead→qualified` },
    xAxis: { type: 'category', data: months, splitArea: { show: true } },
    yAxis: { type: 'category', data: cities, splitArea: { show: true } },
    visualMap: { min: Math.min(...vals), max: Math.max(...vals), calculable: true, orient: 'horizontal',
      left: 'center', bottom: 0, itemWidth: 12, itemHeight: 120, textStyle: { color: v('--text-faint') },
      inRange: { color: ['#3b1d2a', '#7a3b2e', '#c2762e', '#34d399'] } },
    series: [{ type: 'heatmap', data: hdata, label: { show: true, color: '#fff', fontSize: 10, formatter: p => p.value[2] },
      itemStyle: { borderColor: v('--surface-1'), borderWidth: 2, borderRadius: 4 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,.5)' } } }],
  });

  const list = card('Detected Anomalies', `${d.anomalies.length} findings · |z| ≥ 2`); list.style.marginTop = 'var(--s4)';
  if (!d.anomalies.length) list.append(el('div', 'empty', 'No significant anomalies.'));
  else d.anomalies.forEach(a => {
    const it = el('div', `insight ${a.direction === 'drop' ? 'alert' : 'info'}`,
      `<div class="insight-dot"></div><div><div class="insight-title">${a.metric} ${a.direction} · ${a.dimension}</div>
       <div class="insight-detail">${a.value} vs expected ~${a.expected} (<strong>${a.deviation_pct}%</strong>, z=${a.z}) around ${a.label}</div></div>`);
    it.onclick = () => { applyFilter(a.filter); go('funnel'); };
    list.append(it);
  });
  c.append(list);
  // highlight the most anomalous city
  const worst = d.anomalies[0];
  renderCityCR(cr.node, d.city_cr, worst ? (worst.dimension.split(': ')[1]) : null);
};

PAGES.quality = async (c) => {
  skeletonGrid(c, 4, 4);
  let d; try { d = await api('/api/quality'); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';
  const s = d.summary;
  if (!s.available) { c.append(card('Data Quality', '', '<div class="empty">No dbt artifacts found. Build the funnel-warehouse project to populate.</div>')); return; }
  const kg = el('div', 'grid cols-4');
  [['Tests Passed', `${s.tests_passed}/${s.tests_total}`, `${s.pass_rate}% pass`],
   ['Models Built', s.models_built, 'dbt run'],
   ['Last Build', s.elapsed_time ? s.elapsed_time + 's' : '–', 'wall time'],
   ['dbt Version', s.dbt_version || '–', (s.generated_at || '').slice(0, 10)]]
    .forEach(([l, val, sub]) => { const t = card(); t.classList.add('kpi'); t.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; kg.append(t); });
  c.append(kg);

  const row = el('div', 'grid cols-2'); row.style.marginTop = 'var(--s4)';
  const tb = card('Tests by Type', '');
  tb.append(sortableTable([{ key: 'kind', label: 'Test type' }, { key: 'passed', label: 'Passed' }, { key: 'total', label: 'Total' }],
    d.tests, { kind: x => `<span class="pill">${x.replace(/_/g, ' ')}</span>`, passed: (x, r) => `<span class="delta ${x === r.total ? 'up' : 'down'}">${x}</span>` }));
  const fr = card('Mart Freshness', '');
  fr.append(sortableTable([{ key: 'table', label: 'Table' }, { key: 'rows', label: 'Rows' }, { key: 'max_date', label: 'Max date' }],
    d.freshness, { rows: fmtInt }));
  row.append(tb, fr); c.append(row);

  const note = card('Model Lineage'); note.style.marginTop = 'var(--s4)';
  note.innerHTML = `<div style="display:flex;align-items:center;gap:12px;padding:4px 0">
    <div style="width:28px;height:28px;color:var(--accent)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><use href="#i-quality"/></svg></div>
    <div><div style="font-weight:600">View the interactive lineage graph</div><div style="font-size:12px;color:var(--text-dim)">dbt model graph (staging → intermediate → marts) has been moved to its own dedicated page.</div></div>
    <button class="btn" style="margin-left:auto" onclick="go('lineage')">Open Model Lineage</button></div>`;
  c.append(note);
};

PAGES.lineage = async (c) => {
  skeletonGrid(c, 2, 3);
  let d; try { d = await api('/api/quality'); } catch { c.innerHTML = '<div class="empty">Failed.</div>'; return; }
  c.innerHTML = '';

  // Pipeline architecture cards at top
  const archRow = el('div', 'grid cols-3');
  [
    { name: 'Raw / Staging', iconId: 'i-sheet', desc: 'Raw ingestion from source APIs & exports', color: 'var(--c1)', count: 'stg_' },
    { name: 'Intermediate', iconId: 'i-channel', desc: 'Clean, dedupe, type & SCD2', color: 'var(--c5)', count: 'int_' },
    { name: 'Marts', iconId: 'i-database', desc: 'Dimension & fact models for analytics', color: 'var(--good)', count: 'fct_' },
  ].forEach(st => {
    const stc = card(); stc.classList.add('kpi');
    const cnt = d.lineage.nodes ? d.lineage.nodes.filter(n => n.layer === st.count.replace('_', '')).length : 0;
    stc.innerHTML = `<div style="width:28px;height:28px;margin-bottom:8px;color:${st.color}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:100%;height:100%"><use href="#${st.iconId}"/></svg></div>
      <div class="kpi-label">${st.name}</div>
      <div class="kpi-value tnum" style="font-size:22px">${cnt || d.lineage.nodes?.length ? '✓' : '–'}</div>
      <div style="font-size:11px;color:var(--text-dim)">${st.desc}</div>`;
    stc.style.borderTopColor = st.color; stc.style.borderTopWidth = '2px';
    archRow.append(stc);
  });
  c.append(archRow);

  const lin = card('Interactive Lineage Graph', `${d.lineage.nodes?.length ?? 0} nodes · drag to explore · scroll to zoom`);
  lin.style.marginTop = 'var(--s4)'; lin.dataset.tour = 'lineage';
  const ln = el('div'); ln.className = 'chart'; ln.style.height = '600px'; lin.append(ln); c.append(lin);
  if (d.lineage.available && d.lineage.nodes?.length) renderLineage(ln, d.lineage);
  else lin.append(el('div', 'empty', 'No manifest.json found. Build the funnel-warehouse project to generate dbt artifacts.'));
};

function renderLineage(node, g) {
  const layerColors = [v('--c3'), v('--c5'), v('--c6'), v('--c2')];
  chart(node, {
    tooltip: { formatter: p => p.dataType === 'node' ? `<b>${p.data.name}</b><br>${p.data.layer}` : '' },
    legend: [{ data: g.categories.map((c, i) => ({ name: c })), top: 4, textStyle: { color: v('--text-dim') } }],
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true,
      force: { repulsion: 220, edgeLength: [60, 140], gravity: .08 },
      categories: g.categories.map((c, i) => ({ name: c, itemStyle: { color: layerColors[i] } })),
      label: { show: true, color: v('--text'), fontSize: 10, position: 'right' },
      lineStyle: { color: v('--border-strong'), curveness: .15, width: 1.4 },
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 6,
      emphasis: { focus: 'adjacency', lineStyle: { width: 2.5, color: v('--accent') } },
      data: g.nodes.map(n => ({ id: n.id, name: n.name, category: n.category, layer: n.layer, symbolSize: n.layer === 'marts' ? 26 : n.layer === 'source' ? 14 : 20 })),
      links: g.links,
    }],
  });
}

PAGES.sheets = async (c) => {
  let d; try { d = await api('/api/sheets'); } catch { d = null; }
  c.innerHTML = '';
  if (!d || !d.available) { c.append(card('Sheet Sync', '', '<div class="empty">Sheet Sync not initialized.<br>Run <code>python -m sheetsync.seed</code> then <code>python -m sheetsync.run</code>.</div>')); return; }
  renderSheets(c, d);
};

function renderSheets(c, d) {
  // header KPIs + sync button
  const t = d.totals;
  const head = el('div', 'grid cols-4');
  [['Sheets Tracked', d.sheets.length, 'studio front-desk logs'],
   ['Rows Merged', fmtInt(t.rows_merged), 'idempotent MERGE'],
   ['Quarantined', t.quarantined, 'drift held back'],
   ['Deletions Caught', t.deletes, 'vs prior snapshot']]
    .forEach(([l, val, sub]) => { const k = card(); k.classList.add('kpi'); k.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; head.append(k); });
  c.append(head);

  const bar = el('div'); bar.style.cssText = 'display:flex;gap:8px;margin-top:var(--s4)';
  const syncBtn = el('button', 'btn primary', `<svg><use href="#i-play"/></svg> Sync now`);
  syncBtn.dataset.tour = 'sync';
  syncBtn.onclick = async () => { syncBtn.disabled = true; syncBtn.innerHTML = 'Syncing…'; try { await fetch('/api/sheets/sync', { method: 'POST' }); toast('Sync complete'); go('sheets'); } catch { toast('Sync failed'); syncBtn.disabled = false; } };
  bar.append(syncBtn);
  c.append(bar);

  // sync-source catalog: which sources feed the warehouse, and their status
  const srcCard = card('Sync Sources', 'governed pipelines into the warehouse');
  srcCard.style.marginTop = 'var(--s4)';
  const sources = [
    { name: 'Google Sheets', kind: 'Studio front-desk logs', logo: 'GS', c: 'var(--good)', state: 'active', meta: `${d.sheets.length} sheets · ${t.quarantined} quarantined`, jump: true },
    { name: 'PostgreSQL', kind: 'App database (bookings)', logo: 'PG', c: 'var(--c5)', state: 'available', meta: 'CDC or scheduled extract' },
    { name: 'S3 drop folder', kind: 'Partner CSV / Parquet', logo: 'S3', c: 'var(--c6)', state: 'available', meta: 'contract-validated on arrival' },
    { name: 'Excel upload', kind: 'Ad-hoc finance files', logo: 'XL', c: 'var(--c2)', state: 'available', meta: 'drag-drop, schema-checked' },
  ];
  const stbl = el('div'); stbl.style.cssText = 'display:flex;flex-direction:column;gap:8px';
  sources.forEach(s => {
    const row = el('div'); row.style.cssText = 'display:flex;align-items:center;gap:12px;padding:11px 12px;border:1px solid var(--border);border-radius:10px;background:var(--surface-1);' + (s.jump ? 'cursor:pointer' : '');
    row.innerHTML = `<div class="conn-logo" style="width:34px;height:34px;color:${s.c}">${s.logo}</div>
      <div style="flex:1"><div style="font-weight:600">${s.name}</div><div style="font-size:11px;color:var(--text-faint)">${s.kind}</div></div>
      <div style="font-size:11px;color:var(--text-dim);text-align:right">${s.meta}</div>
      <span class="conn-status ${s.state === 'active' ? 'connected' : 'available'}">${s.state === 'active' ? '<span class="live-dot"></span> active' : 'available'}</span>`;
    if (s.jump) row.onclick = () => document.querySelector('#sheetDetail')?.scrollIntoView({ behavior: 'smooth' });
    stbl.append(row);
  });
  srcCard.append(stbl);
  c.append(srcCard);

  const detailHead = el('div', 'card-title');
  detailHead.style.cssText = 'margin-top:var(--s5)';
  detailHead.id = 'sheetDetail';
  detailHead.innerHTML = '<span>Google Sheets · sync detail</span><span class="hint">per-sheet health & drift</span>';
  c.append(detailHead);

  // per-sheet health cards
  const grid = el('div', 'grid cols-3'); grid.style.marginTop = 'var(--s4)';
  d.sheets.forEach(s => {
    const drift = s.drift && s.drift.length;
    const sev = s.status === 'quarantined' ? 'alert' : (s.status.includes('delete') ? 'info' : 'good');
    const k = card();
    k.style.borderColor = drift ? 'var(--bad)' : 'var(--border)';
    let body = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <strong>${s.sheet}</strong><span class="delta ${sev === 'good' ? 'up' : sev === 'alert' ? 'down' : 'flat'}">${s.status}</span></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12px;color:var(--text-dim)">
        <div>In: <strong class="tnum">${fmtInt(s.rows_in)}</strong></div>
        <div>Merged: <strong class="tnum">${fmtInt(s.rows_merged)}</strong></div>
        <div>Errors: <strong class="tnum">${fmtInt(s.rows_error)}</strong></div>
        <div>Deletes: <strong class="tnum">${fmtInt(s.deletes)}</strong></div>
      </div>`;
    if (drift) {
      body += `<div style="margin-top:10px;padding:9px;border-radius:8px;background:var(--bad-dim);border:1px solid rgba(251,113,133,.3)">
        <div style="font-size:11px;color:var(--bad);font-weight:600;display:flex;align-items:center;gap:5px;margin-bottom:4px"><svg style="width:12px;height:12px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> SCHEMA DRIFT · quarantined</div>`;
      s.drift.forEach(dr => {
        body += `<div style="font-size:12px;margin-top:6px">Unknown column <code>${dr.unknown_header}</code><br>
          → suggest <strong>${dr.suggestion}</strong> <span class="pill">${Math.round(dr.confidence * 100)}% conf</span>
          <div style="color:var(--text-faint);font-size:10px;margin-top:2px;font-family:var(--mono)">${dr.evidence}</div>
          <button class="btn" style="margin-top:6px;padding:4px 10px;font-size:11px" data-approve="${dr.unknown_header}|${dr.suggestion}">Approve mapping</button></div>`;
      });
      body += `</div>`;
    }
    if (s.last_sync) body += `<div style="margin-top:8px;font-size:10px;color:var(--text-faint);font-family:var(--mono)">last sync ${s.last_sync} · ${s.duration_ms}ms</div>`;
    k.insertAdjacentHTML('beforeend', body);
    grid.append(k);
  });
  c.append(grid);
  $$('[data-approve]', grid).forEach(b => b.onclick = () => {
    const [hdr, sug] = b.dataset.approve.split('|');
    toast(`Mapping approved: ${hdr} → ${sug}. In production this writes the alias to the contract YAML + re-syncs.`);
    b.disabled = true; b.textContent = 'Approved ✓';
  });

  // recent sync log
  const log = card('Recent Sync Activity', 'audit trail'); log.style.marginTop = 'var(--s4)';
  log.append(sortableTable([
    { key: 'at', label: 'When' }, { key: 'sheet', label: 'Sheet' }, { key: 'status', label: 'Status' },
    { key: 'merged', label: 'Merged' }, { key: 'deletes', label: 'Deletes' }, { key: 'sync_id', label: 'Sync ID' },
  ], d.recent, {
    status: x => `<span class="pill ${x === 'quarantined' ? 'organic' : x.includes('delete') ? 'paid_search' : 'referral'}">${x}</span>`,
    merged: fmtInt, sync_id: x => `<code>${x}</code>`,
  }));
  c.append(log);
}

// ---------- SQL Workspace: IDE-grade ----------
const _SQL_DEFAULT = `-- Explore your warehouse data
-- Ctrl+Enter to run · Click schema tables to insert names
select s.city,
       s.studio_name,
       sum(f.leads) as leads,
       sum(f.purchased) as members,
       count(distinct f.date_day) as active_days
from main_marts.fct_funnel_daily f
join main_marts.dim_studio s on f.studio_key = s.studio_key
group by 1, 2
order by members desc
limit 20`;

if (!state.sqlTabs) {
  state.sqlTabs = [{ id: 1, name: 'Query 1', query: state.sqlPrefill || _SQL_DEFAULT }];
  state.sqlActiveTab = 1;
  state.sqlPrefill = null;
}
if (!state.sqlHistory) {
  try { state.sqlHistory = JSON.parse(localStorage.getItem('grc-sql-history') || '[]'); } catch { state.sqlHistory = []; }
}

PAGES.sql = async (c) => {
  c.innerHTML = '';
  let schemaData = null, wsSchema = null, wsStats = null;
  let lastRows = null, lastCols = null;
  let previewActive = false;

  // --- layout shell ---
  const ws = el('div', 'sql-workspace');
  const schemaPanel = el('div', 'sql-schema');
  const mainArea = el('div', 'sql-main');
  ws.append(schemaPanel, mainArea);
  c.append(ws);

  // ── SCHEMA PANEL ──────────────────────────────────────────
  const sHead = el('div', 'sql-schema-head');
  sHead.innerHTML = '<span>Explorer</span><span>schema</span>';
  const sToggleSide = el('button', 'sql-schema-toggle', '\u00AB');
  sToggleSide.title = 'Toggle sidebar';
  sHead.append(sToggleSide);
  schemaPanel.append(sHead);

  const sSearch = el('div', 'sql-schema-search');
  const sInp = el('input'); sInp.type = 'text'; sInp.placeholder = 'Filter tables\u2026';
  sSearch.append(sInp);
  schemaPanel.append(sSearch);

  const sStats = el('div', 'sql-schema-stats');
  schemaPanel.append(sStats);

  const sBody = el('div', 'sql-schema-body');
  schemaPanel.append(sBody);

  // ── MAIN AREA ─────────────────────────────────────────────
  // tab bar
  const tabBar = el('div', 'sql-tabbar');
  const tabAdd = el('button', 'sql-tab-add', '+');
  const tabActions = el('div', 'sql-tabbar-actions');
  const histBtn = el('button', 'sql-tabbar-btn', '\u{1F4CB}'); histBtn.title = 'Query History';
  const histBadge = el('span'); histBadge.style.cssText = 'position:absolute;top:-2px;right:-4px;background:var(--accent);color:#fff;font-size:8px;border-radius:8px;padding:1px 4px;line-height:1.2;min-width:14px;text-align:center;font-weight:700;display:none;';
  histBtn.style.position = 'relative';
  histBtn.append(histBadge);
  tabActions.append(histBtn);
  const spacer2 = el('div', 'sql-tabbar-spacer');
  tabBar.append(spacer2, tabActions, tabAdd);
  mainArea.append(tabBar);

  // editor wrap
  const edWrap = el('div', 'sql-editor-wrap');
  const gutter = el('div', 'sql-editor-gutter');
  const ta = el('textarea', 'sql-editor'); ta.spellcheck = false; ta.placeholder = 'Write your SQL here\u2026';
  edWrap.append(gutter, ta);
  mainArea.append(edWrap);

  // toolbar
  const tb = el('div', 'sql-toolbar');
  const runBtn = el('button', 'btn primary', '\u25B6 Run'); runBtn.title = 'Ctrl+Enter';
  const expBtn = el('button', 'btn', '\u2B07 CSV'); expBtn.title = 'Export CSV';
  expBtn.disabled = true;
  const fmtBtn = el('button', 'btn', '\u2728 Format');
  const clrBtn = el('button', 'btn', '\u{1F5D1} Clear');
  const tbDiv = el('div', 'sql-toolbar-divider');
  const tbInfo = el('div', 'sql-toolbar-info');
  tbInfo.innerHTML = '<span class="dot"></span> warehouse';
  tb.append(runBtn, expBtn, fmtBtn, clrBtn, tbDiv, tbInfo);
  mainArea.append(tb);

  // results area
  const resArea = el('div', 'sql-results');
  const resBar = el('div', 'sql-results-bar');
  resBar.innerHTML = '<span class="stat">Ready</span><div class="spacer"></div>';
  const resBody = el('div', 'sql-results-body');
  resBody.innerHTML = '<div class="sql-results-empty"><svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg><span>Run a query to see results</span></div>';
  resArea.append(resBar, resBody);
  mainArea.append(resArea);

  // history bottom section
  const histBottom = el('div', 'sql-history-bottom');
  const histBottomInner = el('div', 'sql-history-bottom-inner');
  const histHead = el('div', 'sql-history-head');
  histHead.innerHTML = '<span>Query History</span>';
  const histClear = el('button', null, 'Clear all');
  histHead.append(histClear);
  const histBody = el('div', 'sql-history-body');
  histBottomInner.append(histHead, histBody);
  histBottom.append(histBottomInner);
  mainArea.append(histBottom);

  // info cards
  const infoCards = el('div', 'sql-info-cards');
  for (let i = 0; i < 4; i++) infoCards.append(el('div', 'sql-info-card', '<div class="val">\u2014</div><div class="lbl">\u200B</div>'));
  mainArea.append(infoCards);

  // status bar
  const statusBar = el('div', 'sql-status');
  statusBar.innerHTML = '<span class="dot green"></span><span>Warehouse connected</span><span class="spacer"></span><kbd>\u2303Enter</kbd> run';
  mainArea.append(statusBar);

  // preview overlay
  const previewOverlay = el('div', 'sql-preview-modal');
  previewOverlay.style.display = 'none';
  mainArea.append(previewOverlay);

  // ── state helpers ──
  function saveHistory() {
    localStorage.setItem('grc-sql-history', JSON.stringify(state.sqlHistory.slice(0, 30)));
    updateHistBadge();
    updateInfoCards();
  }
  function addHistory(query) {
    if (!query || !query.trim()) return;
    state.sqlHistory = state.sqlHistory.filter(h => h.query !== query);
    state.sqlHistory.unshift({ query: query.trim(), ts: Date.now() });
    if (state.sqlHistory.length > 30) state.sqlHistory.length = 30;
    saveHistory();
  }
  function getTab() { return state.sqlTabs.find(t => t.id === state.sqlActiveTab) || state.sqlTabs[0]; }
  function saveTab() {
    const t = getTab(); if (t) t.query = ta.value;
  }
  function lineCount() { return (ta.value || '').split('\n').length; }
  function updateGutter() {
    const n = Math.max(lineCount(), 3);
    gutter.innerHTML = Array.from({ length: n }, (_, i) => `<span>${i + 1}</span>`).join('');
  }
  function syncGutterScroll() { gutter.scrollTop = ta.scrollTop; }
  ta.addEventListener('scroll', syncGutterScroll);
  ta.addEventListener('input', () => { updateGutter(); saveTab(); });

  // global escape handler for overlays
  document.addEventListener('keydown', function sqlEsc(e) {
    if (e.key === 'Escape') {
      if (previewActive) { previewOverlay.style.display = 'none'; previewActive = false; }
      if (histBottom.classList.contains('open')) histBottom.classList.remove('open');
    }
  });

  function insert(txt) {
    ta.focus();
    if (ta.selectionStart !== ta.selectionEnd) {
      const s = ta.selectionStart; ta.value = ta.value.slice(0, s) + txt + ta.value.slice(ta.selectionEnd);
      ta.selectionStart = ta.selectionEnd = s + txt.length;
    } else {
      const s = ta.selectionStart; ta.value = ta.value.slice(0, s) + txt + ta.value.slice(s);
      ta.selectionStart = ta.selectionEnd = s + txt.length;
    }
    updateGutter(); saveTab();
  }

  // ── RENDER TABS ──
  function renderTabs() {
    tabBar.innerHTML = '';
    const left = el('div'); left.style.cssText = 'display:flex;align-items:center;overflow-x:auto;flex:1';
    state.sqlTabs.forEach(t => {
      const tb2 = el('div', 'sql-tab' + (t.id === state.sqlActiveTab ? ' active' : ''));
      tb2.textContent = t.name;
      const close = el('button', 'close-tab', '\u00D7');
      close.onclick = (e) => { e.stopPropagation(); closeTab(t.id); };
      tb2.append(close);
      tb2.onclick = () => switchTab(t.id);
      left.append(tb2);
    });
    tabBar.append(left, spacer2, tabActions, tabAdd);
    ta.value = getTab().query || '';
    updateGutter();
  }
  function switchTab(id) {
    saveTab();
    state.sqlActiveTab = id;
    renderTabs();
    clearResults();
  }
  function addTab() {
    saveTab();
    const id = Date.now();
    const n = state.sqlTabs.length + 1;
    state.sqlTabs.push({ id, name: 'Query ' + n, query: '' });
    state.sqlActiveTab = id;
    renderTabs();
    ta.focus();
  }
  function closeTab(id) {
    if (state.sqlTabs.length <= 1) { addTab(); }
    const idx = state.sqlTabs.findIndex(t => t.id === id);
    if (idx === -1) return;
    state.sqlTabs.splice(idx, 1);
    if (state.sqlActiveTab === id) {
      state.sqlActiveTab = state.sqlTabs[Math.min(idx, state.sqlTabs.length - 1)].id;
    }
    renderTabs();
  }
  tabAdd.onclick = addTab;

  // ── RESULTS ──
  function clearResults() {
    resBar.innerHTML = '<span class="stat">Ready</span><div class="spacer"></div>';
    resBody.innerHTML = '<div class="sql-results-empty"><svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg><span>Run a query to see results</span></div>';
    lastRows = null; lastCols = null; expBtn.disabled = true;
  }

  function renderResults(d) {
    if (!d.rows || !d.rows.length) {
      resBar.innerHTML = '<span class="stat">0 rows</span><div class="spacer"></div>';
      resBody.innerHTML = '<div class="empty-state"><span>Query executed successfully</span><code>0 rows returned</code></div>';
      expBtn.disabled = true; return;
    }
    const label = d.rowcount + ' row' + (d.rowcount !== 1 ? 's' : '') +
      (d.capped ? ' (capped at 1000)' : '') + ' \u00B7 ' + d.ms + ' ms';
    resBar.innerHTML = `<span class="stat"><b>${d.rowcount.toLocaleString()}</b> rows \u00B7 ${d.ms} ms</span>` +
      (d.capped ? '<span style="color:var(--warn)">capped at 1000</span>' : '') +
      '<div class="spacer"></div>' +
      '<button class="copy-btn" title="Copy as TSV">Copy</button>';
    resBar.querySelector('.copy-btn').onclick = () => copyResults(d);

    const wrap = el('div'); wrap.style.cssText = 'display:inline-block;min-width:100%';
    const t = el('table', 'data');
    const thead = el('thead'); const trh = el('tr');
    d.columns.forEach(c => trh.append(el('th', null, c)));
    thead.append(trh); t.append(thead);
    const tb2 = el('tbody');
    d.rows.forEach(row => {
      const tr = el('tr');
      row.forEach(v => { const td = el('td'); td.textContent = v == null ? '' : String(v); tr.append(td); });
      tb2.append(tr);
    });
    t.append(tb2); wrap.append(t);
    resBody.innerHTML = ''; resBody.append(wrap);
    lastRows = d.rows; lastCols = d.columns; expBtn.disabled = false;
  }

  function copyResults(d) {
    const lines = [d.columns.join('\t'), ...d.rows.map(r => r.map(v => v == null ? '' : String(v)).join('\t'))];
    navigator.clipboard.writeText(lines.join('\n')).then(() => toast('Copied')).catch(() => {});
  }

  // ── RUN QUERY ──
  async function run() {
    const q = ta.value.trim();
    if (!q) { toast('Query is empty'); return; }
    saveTab();
    runBtn.disabled = true; runBtn.innerHTML = '\u23F3 Running\u2026';
    resBar.innerHTML = '<span class="stat">Running\u2026</span><div class="spacer"></div>';
    resBody.innerHTML = '<div class="skel" style="height:60px;margin:10px"></div>';
    expBtn.disabled = true;
    try {
      const r = await fetch('/api/sql', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) });
      const d = await r.json();
      if (!d.ok) { resBar.innerHTML = '<span class="stat" style="color:var(--bad)">Error</span>'; resBody.innerHTML = `<div class="sql-err">${d.error}</div>`; return; }
      renderResults(d);
      addHistory(q);
      renderHistory();
    } catch (e) { resBar.innerHTML = '<span class="stat" style="color:var(--bad)">Error</span>'; resBody.innerHTML = `<div class="sql-err">Request failed: ${e.message}</div>`; }
    runBtn.disabled = false; runBtn.innerHTML = '\u25B6 Run';
  }
  runBtn.onclick = run;
  ta.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); }
    if (e.key === 'Tab') { e.preventDefault(); insert('  '); }
  });

  // ── EXPORT CSV ──
  expBtn.onclick = () => {
    if (!lastRows || !lastCols) return;
    const csv = [lastCols.join(','), ...lastRows.map(r => r.map(v => { const s = String(v ?? ''); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }).join(','))].join('\n');
    const a = el('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'grc_query.csv'; a.click();
    toast('CSV downloaded');
  };

  // ── FORMAT SQL ──
  fmtBtn.onclick = async () => {
    const q = ta.value.trim();
    if (!q) return;
    fmtBtn.disabled = true; fmtBtn.textContent = '\u23F3\u2026';
    try {
      const r = await fetch('/api/sql/format', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) });
      const d = await r.json();
      if (d.formatted) { ta.value = d.formatted; updateGutter(); saveTab(); toast('Formatted'); }
    } catch {}
    fmtBtn.disabled = false; fmtBtn.innerHTML = '\u2728 Format';
  };

  // ── CLEAR ──
  clrBtn.onclick = () => { ta.value = ''; updateGutter(); saveTab(); clearResults(); ta.focus(); };

  // ── HISTORY ──
  histBtn.onclick = () => {
    histBottom.classList.toggle('open');
    if (histBottom.classList.contains('open')) renderHistory();
  };
  histClear.onclick = () => { state.sqlHistory = []; saveHistory(); renderHistory(); toast('History cleared'); };
  function updateHistBadge() { histBadge.textContent = state.sqlHistory.length || ''; histBadge.style.display = state.sqlHistory.length ? 'inline' : 'none'; }
  function renderHistory() {
    updateHistBadge();
    if (!state.sqlHistory.length) { histBody.innerHTML = '<div class="sql-history-empty">No queries yet</div>'; return; }
    histBody.innerHTML = '';
    state.sqlHistory.slice(0, 25).forEach(h => {
      const item = el('div', 'sql-history-item');
      const short = h.query.length > 80 ? h.query.slice(0, 80) + '\u2026' : h.query;
      item.innerHTML = `<span class="hq">${short.replace(/</g,'&lt;')}</span><span class="hm">${timeAgo(new Date(h.ts).toISOString())}</span>`;
      item.onclick = () => { ta.value = h.query; updateGutter(); saveTab(); histBottom.classList.remove('open'); ta.focus(); };
      histBody.append(item);
    });
  }

  // ── SCHEMA RENDER ──
  function updateInfoCards() {
    const cards = infoCards.querySelectorAll('.sql-info-card');
    if (cards.length >= 4 && wsStats) {
      cards[0].innerHTML = `<div class="val">${wsStats.totalTables || wsStats.total_tables}</div><div class="lbl">Tables</div>`;
      cards[1].innerHTML = `<div class="val">${wsStats.totalSchemas || wsStats.total_schemas}</div><div class="lbl">Schemas</div>`;
      cards[2].innerHTML = `<div class="val">${wsStats.totalColumns || wsStats.total_columns}</div><div class="lbl">Columns</div>`;
      cards[3].innerHTML = `<div class="val">${state.sqlHistory.length}</div><div class="lbl">Recent Queries</div>`;
    }
  }
  async function loadSchema() {
    try {
      const [d, st] = await Promise.all([api('/api/sql/schema'), api('/api/sql/stats')]);
      schemaData = d.tables || [];
      wsStats = st;
      sStats.innerHTML = `<span>${st.totalTables || st.total_tables} tables</span><span>${st.totalSchemas || st.total_schemas} schemas</span>`;
      updateInfoCards();
      renderSchema('');
    } catch { sBody.innerHTML = '<div class="empty" style="padding:20px;text-align:center;color:var(--text-faint);font-size:11px">Schema unavailable</div>'; }
  }

  function renderSchema(filter) {
    if (!schemaData) return;
    const f = (filter || '').toLowerCase();
    sBody.innerHTML = '';
    const groups = {};
    schemaData.forEach(t => {
      if (f && !t.table.toLowerCase().includes(f) && !t.schema.toLowerCase().includes(f)) return;
      if (!groups[t.schema]) groups[t.schema] = [];
      groups[t.schema].push(t);
    });
    Object.keys(groups).sort().forEach(schema => {
      const grp = el('div', 'sql-schema-grp');
      const grpH = el('div', 'sql-schema-grp-header');
      grpH.innerHTML = `<span class="arrow">\u25BC</span>\u{1F4E6} ${schema}<span class="count">${groups[schema].length}</span>`;
      grp.append(grpH);
      const tblList = el('div');
      groups[schema].forEach(t => {
        const tblEl = el('div', 'sql-schema-tbl');
        const tblH = el('div', 'sql-schema-tbl-header');
        tblH.innerHTML = `\u{1F4CB} ${t.table}<span class="preview-btn">\u{1F50D}</span>`;
        tblH.onclick = (e) => {
          if (e.target.closest('.preview-btn')) return;
          const next = tblH.nextElementSibling;
          if (next) next.classList.toggle('open');
        };
        tblH.querySelector('.preview-btn').onclick = (e) => {
          e.stopPropagation();
          previewTable(schema, t.table);
        };
        const colsEl = el('div', 'sql-schema-cols');
        (t.columns || []).forEach(col => {
          const ce = el('div', 'sql-schema-col');
          ce.innerHTML = `<span>${col.name}</span><span class="col-type">${col.type}</span>`;
          ce.onclick = () => insert(col.name);
          colsEl.append(ce);
        });
        tblEl.append(tblH, colsEl);
        tblList.append(tblEl);
      });
      grp.append(tblList);
      sBody.append(grp);
    });
  }

  sInp.oninput = () => renderSchema(sInp.value);

  // ── TABLE PREVIEW ──
  async function previewTable(schema, table) {
    previewActive = true;
    previewOverlay.style.display = 'flex';
    previewOverlay.style.flexDirection = 'column';
    const closePreview = () => { previewOverlay.style.display = 'none'; previewActive = false; };
    previewOverlay.innerHTML = `
      <div class="sql-preview-head">
        <span style="font-size:13px">\u{1F50D}</span> ${schema}.${table}
        <button class="close-btn">\u2190 Back</button>
      </div>
      <div class="sql-preview-body"><div class="loading">Loading\u2026</div></div>`;
    previewOverlay.querySelector('.close-btn').onclick = closePreview;
    previewOverlay.querySelector('.sql-preview-head').onclick = (e) => { if (e.target.closest('.close-btn')) return; closePreview(); };
    previewOverlay.onclick = (e) => { if (e.target === previewOverlay) closePreview(); };
    const escHandler = (e) => { if (e.key === 'Escape') { closePreview(); document.removeEventListener('keydown', escHandler); } };
    document.addEventListener('keydown', escHandler);
    try {
      const d = await api(`/api/sql/preview?schema=${encodeURIComponent(schema)}&table=${encodeURIComponent(table)}&limit=50`);
      if (!d.ok) { previewOverlay.querySelector('.sql-preview-body').innerHTML = `<div class="sql-err">${d.error}</div>`; return; }
      const body = previewOverlay.querySelector('.sql-preview-body');
      if (!d.columns || !d.columns.length) { body.innerHTML = '<div class="empty-state">No columns</div>'; return; }
      const wrap = el('div'); wrap.style.cssText = 'display:inline-block;min-width:100%';
      const t = el('table', 'data');
      const thead = el('thead'); const trh = el('tr');
      d.columns.forEach(c => trh.append(el('th', null, c)));
      thead.append(trh); t.append(thead);
      const tb2 = el('tbody');
      (d.rows || []).forEach(row => {
        const tr = el('tr');
        row.forEach(v => { const td = el('td'); td.textContent = v == null ? '' : String(v); tr.append(td); });
        tb2.append(tr);
      });
      t.append(tb2); wrap.append(t);
      body.innerHTML = `<div style="padding:6px 12px;font-size:10px;color:var(--text-faint);border-bottom:1px solid var(--border)">${d.rowcount || 0} rows · preview · <span style="opacity:.6">ESC or ← Back to close</span></div>`;
      body.append(wrap);
    } catch { previewOverlay.querySelector('.sql-preview-body').innerHTML = '<div class="sql-err">Preview failed</div>'; }
  }

  // ── TOGGLE SIDEBAR ──
  sToggleSide.onclick = () => {
    ws.classList.toggle('collapsed');
    sToggleSide.textContent = ws.classList.contains('collapsed') ? '\u00BB' : '\u00AB';
  };

  // ── INIT ──
  renderTabs();
  loadSchema();
  updateHistBadge();
  ta.focus();
};

PAGES.connectors = async (c) => {
  c.innerHTML = '';
  const hero = card(); hero.classList.add('hero-card');
  hero.innerHTML = `<div class="hero-mesh"></div>
    <div style="font-size:var(--fs-xl);font-weight:700;letter-spacing:-.02em">Data Sources</div>
    <div style="color:var(--text-dim);margin-top:6px;max-width:680px;line-height:1.6">
      Two kinds here, both real: the <b>warehouse</b> (always on) and <b>Sheet Sync</b> (see its own page)
      are built in. Below, register your own local CSV: it's loaded into DuckDB and immediately
      queryable from <a href="#" onclick="go('sql');return false">SQL Workspace</a> as
      <code>custom.&lt;table&gt;</code>, and the Data/Analytics Engineer agents mention it in their
      real answers. Nothing here is a mockup: an empty list below means no CSV has been registered yet.</div>`;
  c.append(hero);

  let live = { warehouse: '—', sheets: '—' };
  try { const q = await api('/api/quality'); live.warehouse = q.summary?.models_built ?? '—'; } catch {}
  try { const s = await api('/api/sheets'); if (s.available) live.sheets = s.sheets.length; } catch {}

  let sources = [];
  try { sources = (await api('/api/datasources')).sources || []; } catch {}

  const kpis = el('div', 'grid cols-4'); kpis.style.marginTop = 'var(--s4)';
  [['Warehouse Models', live.warehouse, 'built by dbt · read-only'],
   ['Sheets Tracked', live.sheets, 'governed sync'],
   ['Custom Sources', sources.length, 'CSV, queryable now'],
   ['Rows (custom)', fmtInt(sources.reduce((a, s) => a + (s.row_count || 0), 0)), 'across custom sources']]
    .forEach(([l, val, sub]) => { const k = card(); k.classList.add('kpi'); k.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; kpis.append(k); });
  c.append(kpis);

  const formCard = card(); formCard.style.marginTop = 'var(--s4)';
  formCard.innerHTML = `<div style="font-weight:600;margin-bottom:10px">Register a CSV</div>
    <form id="dsForm" style="display:flex;gap:8px;flex-wrap:wrap">
      <input id="dsName" placeholder="Source name" style="flex:1;min-width:160px" required>
      <input id="dsPath" placeholder="Local path, e.g. /home/you/data.csv" style="flex:2;min-width:240px" required>
      <button class="btn primary" type="submit">Add</button>
    </form>
    <div id="dsErr" style="color:var(--danger,#f87171);font-size:12px;margin-top:6px;display:none"></div>`;
  c.append(formCard);
  formCard.querySelector('#dsForm').onsubmit = async e => {
    e.preventDefault();
    const name = formCard.querySelector('#dsName').value.trim();
    const path = formCard.querySelector('#dsPath').value.trim();
    const errEl = formCard.querySelector('#dsErr');
    errEl.style.display = 'none';
    try {
      const r = await fetch('/api/datasources', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name, path }) });
      const body = await r.json();
      if (!r.ok || body.ok === false) throw new Error(body.error || 'failed');
      go('connectors'); // reload the page to show the new source
    } catch (err) {
      errEl.textContent = err.message || 'Could not add source. Check the path exists on this machine.';
      errEl.style.display = '';
    }
  };

  const grid = el('div', 'grid cols-3'); grid.style.marginTop = 'var(--s4)';
  if (sources.length === 0) {
    grid.innerHTML = `<div style="color:var(--text-faint);font-size:13px">No custom sources registered yet.</div>`;
  }
  sources.forEach(s => {
    const card_ = card(); card_.classList.add('conn');
    card_.innerHTML = `
      <div class="conn-head">
        <div class="conn-logo" style="color:#34d399">CSV</div>
        <div><div class="conn-name">${s.name}</div><div class="conn-kind">${s.columns.length} columns · ${fmtInt(s.row_count)} rows</div></div>
      </div>
      <div class="conn-desc">custom.${s.table}<br><span style="color:var(--text-faint);font-size:11px">${s.path}</span></div>
      <div class="conn-foot"><span class="conn-status connected"><span class="live-dot"></span> Queryable</span>
        <button class="btn ghost" style="padding:2px 8px" data-id="${s.id}">Remove</button></div>`;
    card_.querySelector('button').onclick = async e => {
      e.stopPropagation();
      await fetch(`/api/datasources/${s.id}`, { method: 'DELETE' });
      go('connectors');
    };
    grid.append(card_);
  });
  c.append(grid);
};

// ---------- Member Origins (map + flow lines) ----------
let _worldReady = false;
async function ensureWorldMap() {
  if (_worldReady || (window.echarts && echarts.getMap && echarts.getMap('world'))) { _worldReady = true; return true; }
  try {
    const r = await originalFetch('/vendor/world.json');
    if (r.ok) { echarts.registerMap('world', await r.json()); _worldReady = true; return true; }
  } catch { /* fall through */ }
  return false;
}

PAGES.geoflows = async (c) => {
  c.innerHTML = '';
  let d; try { d = await api('/api/geo'); } catch { d = null; }
  if (!d || !d.available) { c.append(card('Member Origins', '', '<div class="empty">Geo data not found. Run <code>python -m data_gen.geo_flows</code>.</div>')); return; }

  // ---- Enhanced KPIs with location intelligence context ----
  const origins = d.cities.filter(x => x.kind === 'origin');
  const hubs = d.cities.filter(x => x.kind === 'hub');
  const top10 = [...origins].sort((a, b) => b.members - a.members).slice(0, 10);
  const topPct = top10.reduce((a, b) => a + b.members, 0) / d.totals.members * 100;
  const avgDiversity = origins.reduce((a, b) => a + (b.diversity || 0), 0) / origins.length;
  const continentMap = {
    'Tokyo': 'Asia','Seoul':'Asia','Shanghai':'Asia','Hong Kong':'Asia',
    'Mumbai':'Asia','Delhi':'Asia','Bangkok':'Asia','Jakarta':'Asia',
    'Manila':'Asia','Kuala Lumpur':'Asia','Taipei':'Asia','Ho Chi Minh City':'Asia','Bengaluru':'Asia',
    'Sydney':'Oceania','Melbourne':'Oceania','Auckland':'Oceania',
    'Paris':'Europe','Berlin':'Europe','Madrid':'Europe','Rome':'Europe',
    'Amsterdam':'Europe','Dublin':'Europe','Stockholm':'Europe','Lisbon':'Europe',
    'Warsaw':'Europe','Vienna':'Europe','Istanbul':'Europe','Dubai':'Asia',
    'Cairo':'Africa','Lagos':'Africa','Johannesburg':'Africa','Nairobi':'Africa',
    'Tel Aviv':'Asia','Manchester':'Europe',
    'Toronto':'N.America','Chicago':'N.America','Los Angeles':'N.America',
    'Mexico City':'N.America','Miami':'N.America','Vancouver':'N.America',
    'Boston':'N.America','Houston':'N.America','Montreal':'N.America',
    'Sao Paulo':'S.America','Bogota':'S.America','Buenos Aires':'S.America',
    'Lima':'S.America','Santiago':'S.America',
  };
  const byContinent = {};
  origins.forEach(o => {
    const c = continentMap[o.name] || 'Other';
    byContinent[c] = (byContinent[c] || 0) + o.members;
  });

  const kg = el('div', 'grid cols-4');
  [['Member Reach', fmtInt(d.totals.members), 'across origin cities'],
   ['Top-10 Concentration', topPct.toFixed(1) + '%', top10[0].name + ' → ' + top10[9].name],
   ['Avg Diversity Index', (avgDiversity * 100).toFixed(1) + '%', 'multi-origin mix per city'],
   ['Continent Reach', Object.keys(byContinent).length, 'continents represented']]
    .forEach(([l, val, sub], i) => { const t = card(); t.classList.add('kpi', 'reveal'); t.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; kg.append(t); });
  c.append(kg);

  // ---- Map + Intelligence panels side by side ----
  const mainRow = el('div', 'grid cols-3'); mainRow.style.marginTop = 'var(--s4)';

  // Map (span 2)
  const mapCard = card('Global Member Flows', 'drag to pan · scroll to zoom · bubble size = members');
  mapCard.classList.add('span-2');
  const node = el('div'); node.style.height = '560px'; mapCard.append(node);
  mainRow.append(mapCard);

  // Intelligence sidebar
  const intelCol = el('div'); intelCol.style.cssText = 'display:flex;flex-direction:column;gap:var(--s4)';

  // Panel 1: Top origin cities table
  const topCard = card('Top Origin Cities', 'by member contribution');
  const tblWrap = el('div'); tblWrap.style.cssText = 'max-height:280px;overflow-y:auto';
  const tbl = el('table', 'data');
  tbl.innerHTML = `<thead><tr><th>Rank</th><th>City</th><th>Hub</th><th style="text-align:right">Members</th><th style="text-align:right">%</th></tr></thead><tbody>
    ${top10.map((o, i) => `<tr><td>${i + 1}</td><td><strong>${o.name}</strong></td><td><span class="pill" style="font-size:10px">${o.hub}</span></td><td style="text-align:right">${fmtInt(o.members)}</td><td style="text-align:right">${(o.members / d.totals.members * 100).toFixed(1)}%</td></tr>`).join('')}
  </tbody>`;
  tblWrap.append(tbl); topCard.append(tblWrap);
  intelCol.append(topCard);

  // Panel 2: Hub flow breakdown
  const flowCard = card('Hub Flow Distribution', 'member destination');
  const HUBC = { ARD: v('--c4'), BRW: v('--c6'), CRL: v('--c5') };
  const hubList = el('div'); hubList.style.cssText = 'display:flex;flex-direction:column;gap:10px';
  d.hubs.forEach(h => {
    const tot = d.hub_totals[h.id];
    const pct = (tot / d.totals.members * 100).toFixed(1);
    const hCities = origins.filter(o => o.hub === h.id);
    const maxH = Math.max(...hCities.map(o => o.members), 1);
    const topH = [...hCities].sort((a, b) => b.members - a.members).slice(0, 3);
    const hdiv = el('div'); hdiv.style.cssText = 'padding:10px 12px;background:var(--surface-2);border-radius:9px;border:1px solid var(--border)';
    hdiv.innerHTML = `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
      <div style="display:flex;align-items:center;gap:8px">
        <span style="width:10px;height:10px;border-radius:50%;background:${HUBC[h.id]}"></span>
        <strong>${h.name}</strong>
      </div>
      <div><span class="tnum" style="font-size:18px;font-weight:700">${fmtInt(tot)}</span> <span style="font-size:11px;color:var(--text-faint)">(${pct}%)</span></div>
    </div>
    <div style="font-size:11px;color:var(--text-faint)">Top origins: ${topH.map(o => o.name).join(', ')}</div>
    <div style="margin-top:6px;height:4px;border-radius:4px;background:var(--surface-3);overflow:hidden">
      <div style="height:100%;width:${pct}%;border-radius:4px;background:${HUBC[h.id]}"></div>
    </div>`;
    hubList.append(hdiv);
  });
  flowCard.append(hubList);
  intelCol.append(flowCard);
  mainRow.append(intelCol);
  c.append(mainRow);

  const maxM = Math.max(...origins.map(x => x.members));
  const ok = await ensureWorldMap();
  if (!ok) {
    mapCard.append(el('div', 'empty', 'World map unavailable (offline?). Flows hidden, charts below still active.'));
    // don't return, let charts below render
  } else {

  const flows = d.flows.map(f => ({ coords: [f.from, f.to], value: f.value, hub: f.hub }));
  const byHub = {};
  flows.forEach(f => (byHub[f.hub] = byHub[f.hub] || []).push(f));

  const land = document.documentElement.dataset.theme === 'light' ? '#e9e2cc' : '#0c3a47';
  const lineSeries = Object.entries(byHub).flatMap(([hub, arr]) => ([
    { type: 'lines', coordinateSystem: 'geo', zlevel: 1, effect: { show: true, period: 5, trailLength: 0.5, symbol: 'circle', symbolSize: 2.4, color: HUBC[hub] },
      lineStyle: { color: HUBC[hub], width: 0, curveness: 0.32, opacity: 0.6 }, data: arr },
    { type: 'lines', coordinateSystem: 'geo', zlevel: 0,
      lineStyle: { color: HUBC[hub], width: 0.6, opacity: 0.16, curveness: 0.32 }, data: arr },
  ]));

  chart(node, {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: v('--surface-3'), borderColor: v('--border-strong'),
      textStyle: { color: v('--text') }, formatter: p => p.seriesType === 'lines'
        ? `${p.data.value.toLocaleString()} members` : `<b>${p.name}</b><br>${(p.value[2] || 0).toLocaleString()} members` },
    geo: { map: 'world', roam: true, silent: true, zoom: 1.15, center: [20, 25],
      itemStyle: { areaColor: land, borderColor: v('--border-strong'), borderWidth: 0.6 },
      emphasis: { disabled: true }, scaleLimit: { min: 0.8, max: 6 } },
    series: [
      ...lineSeries,
      { type: 'scatter', coordinateSystem: 'geo', zlevel: 2,
        data: origins.map(o => ({ name: o.name, value: [o.lng, o.lat, o.members], hub: o.hub })),
        symbolSize: v => 4 + Math.sqrt(v[2] / maxM) * 22,
        itemStyle: { color: p => HUBC[p.data.hub], opacity: 0.85, borderColor: v('--bg'), borderWidth: 0.5 } },
      { type: 'effectScatter', coordinateSystem: 'geo', zlevel: 3, rippleEffect: { scale: 3, brushType: 'stroke' },
        data: hubs.map(h => ({ name: h.name, value: [h.lng, h.lat, h.members] })),
        symbolSize: 16, itemStyle: { color: v('--accent'), shadowBlur: 14, shadowColor: v('--accent') },
        label: { show: true, formatter: '{b}', position: 'right', color: v('--text'), fontWeight: 600, fontSize: 11 } },
    ],
  });
  }  // end else (map loaded)

  // ---- Location Intelligence Charts ----
  const chartRow = el('div', 'grid cols-3'); chartRow.style.marginTop = 'var(--s4)';

  // Chart 1: Members by continent (bar)
  const contCard = chartCard('Members by Continent', 'origin distribution');
  chartRow.append(contCard.card);
  // Chart 2: Top 10 cities (horizontal bar)
  const cityCard = chartCard('Top 10 Origin Cities', 'ranked by members', 'short');
  chartRow.append(cityCard.card);
  // Chart 3: Hub member share (pie)
  const hubPie = chartCard('Hub Member Share', '% of total');
  chartRow.append(hubPie.card);
  // MUST append to DOM before echarts.init(): it needs layout dimensions
  c.append(chartRow);

  const contSorted = Object.entries(byContinent).sort((a, b) => b[1] - a[1]);
  const contColors = {
    'Asia': v('--c1'), 'Europe': v('--c5'), 'N.America': v('--c4'),
    'S.America': v('--c6'), 'Africa': v('--warn'), 'Oceania': v('--good')
  };
  chart(contCard.node, {
    xAxis: { type: 'category', data: contSorted.map(([k]) => k), axisLabel: { rotate: 0 } },
    yAxis: { type: 'value', axisLabel: { formatter: x => fmtInt(x) } },
    series: [{
      type: 'bar', barWidth: '56%',
      data: contSorted.map(([k, v]) => ({ value: v, itemStyle: { color: contColors[k] || v('--c1'), borderRadius: [6, 6, 0, 0] } })),
    }],
  });

  chart(cityCard.node, {
    grid: { left: 80, right: 20, top: 10, bottom: 10 },
    xAxis: { type: 'value', axisLabel: { formatter: x => fmtInt(x) } },
    yAxis: { type: 'category', data: [...top10].reverse().map(o => o.name), axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar', barWidth: '62%',
      data: [...top10].reverse().map(o => ({ value: o.members, itemStyle: { color: HUBC[o.hub], borderRadius: [0, 6, 6, 0] } })),
    }],
  });

  chart(hubPie.node, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['38%', '65%'], center: ['50%', '50%'],
      label: { color: v('--text-dim'), formatter: '{b}\n{d}%' },
      itemStyle: { borderColor: v('--surface-1'), borderWidth: 3 },
      data: d.hubs.map(h => ({ name: h.name, value: d.hub_totals[h.id], itemStyle: { color: HUBC[h.id] } })),
    }],
  });

  // ---- Flow density: origin city scatter (members vs diversity) ----
  const row3 = el('div', 'grid cols-2'); row3.style.marginTop = 'var(--s4)';
  const densCard = chartCard('City Intelligence: Members vs Diversity', 'bubble = continent · larger = more members');
  densCard.card.classList.add('span-2');
  row3.append(densCard.card);
  c.append(row3);

  const contColorMap = { 'Asia': v('--c1'), 'Europe': v('--c5'), 'N.America': v('--c4'),
    'S.America': v('--c6'), 'Africa': v('--warn'), 'Oceania': v('--good'), 'Other': v('--text-faint') };
  chart(densCard.node, {
    grid: { left: 60, bottom: 50 },
    xAxis: { type: 'value', name: 'Member Count', axisLabel: { formatter: x => fmtInt(x) } },
    yAxis: { type: 'value', name: 'Diversity Index', axisLabel: { formatter: x => (x * 100).toFixed(0) + '%' }, max: 1 },
    tooltip: { formatter: p => `<b>${p.data[3]}</b><br>Members: ${fmtInt(p.data[0])}<br>Diversity: ${(p.data[1] * 100).toFixed(0)}%<br>Continent: ${p.data[4]}` },
    series: [{
      type: 'scatter', symbolSize: d => 10 + Math.sqrt(d[0] / maxM) * 18,
      data: origins.map(o => [o.members, o.diversity, o.hub, o.name, continentMap[o.name] || 'Other']),
      itemStyle: { color: p => contColorMap[p.data[4]] || v('--text-faint'), opacity: 0.75 },
    }],
  });

  // ---- Origin city insight cards ----
  const row4 = el('div', 'grid cols-3'); row4.style.marginTop = 'var(--s4)';
  // Highest diversity
  const mostDiv = [...origins].sort((a, b) => (b.diversity || 0) - (a.diversity || 0))[0];
  // Top hub growth
  const bestHub = [...d.hubs].sort((a, b) => d.hub_totals[b.id] - d.hub_totals[a.id])[0];
  // Continent leader
  const topCont = contSorted[0];
  const insights = [
    { label: 'Most Diverse Origin', val: mostDiv.name, sub: `Diversity ${(mostDiv.diversity * 100).toFixed(0)}% · multi-source member mix`, color: v('--c5') },
    { label: 'Largest Hub', val: bestHub.name, sub: `${fmtInt(d.hub_totals[bestHub.id])} members from ${origins.filter(o => o.hub === bestHub.id).length} cities`, color: v('--c4') },
    { label: 'Top Continent', val: topCont[0], sub: `${fmtInt(topCont[1])} members · ${(topCont[1] / d.totals.members * 100).toFixed(0)}% of total`, color: v('--c1') },
  ];
  insights.forEach(ins => {
    const k = card();
    k.innerHTML = `<div style="font-size:var(--fs-xs);color:var(--text-faint);text-transform:uppercase;letter-spacing:.05em">${ins.label}</div>
      <div style="font-size:var(--fs-xl);font-weight:700;margin:4px 0;color:${ins.color}">${ins.val}</div>
      <div style="font-size:var(--fs-sm);color:var(--text-dim)">${ins.sub}</div>`;
    row4.append(k);
  });
  c.append(row4);
};

// ---------- AI Agents hub ----------
const STATUS_COLOR = { active: 'var(--good)', busy: 'var(--warn)', idle: 'var(--text-faint)', orchestrator: 'var(--accent)' };

function agentSkeletonCard() {
  const s = el('div', 'card agent-card agent-skelly');
  s.innerHTML = `
    <div class="agent-top">
      <div class="skel" style="width:40px;height:40px;border-radius:11px"></div>
      <div style="flex:1">
        <div class="skel" style="width:60%;height:12px"></div>
        <div class="skel" style="width:80%;height:8px;margin-top:8px"></div>
      </div>
    </div>
    <div style="display:flex;gap:5px">
      <span class="skel" style="width:40px;height:18px;border-radius:14px"></span>
      <span class="skel" style="width:50px;height:18px;border-radius:14px"></span>
      <span class="skel" style="width:35px;height:18px;border-radius:14px"></span>
    </div>
    <div class="skel" style="width:100%;height:6px;border-radius:6px;margin-top:4px"></div>
    <div style="display:flex;gap:8px">
      <div class="skel" style="flex:1;height:30px;border-radius:8px"></div>
      <div class="skel" style="flex:1;height:30px;border-radius:8px"></div>
    </div>`;
  return s;
}

async function renderEngineeringLoop(c) {
  const box = card(); box.style.marginTop = 'var(--s4)';
  box.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
      <div style="font-weight:650;font-size:14px">🛠️ Autonomous Engineering Loop</div>
      <span class="chip" style="font-size:10px;padding:2px 8px;pointer-events:none">Owners only</span>
    </div>
    <div class="hint" style="margin-bottom:10px;max-width:720px;line-height:1.6">
      Describe a feature in plain language. An LLM writes the code, the full test suite has to pass
      before anything is kept (a broken attempt is discarded automatically, never applied), and a
      passing change is committed to this app's own git history by itself, no one reviews the diff first.
      New endpoints appear under <code>/api/agent_features/…</code> after you restart the server.
      Needs an <a href="#" onclick="$('#aiSettings').click();return false">engineering-loop model connected</a> first.
    </div>
    <div id="engFeaturesList" style="margin-bottom:12px"></div>
    <form id="engForm" style="display:flex;flex-direction:column;gap:8px">
      <textarea class="input" id="engInstruction" rows="2" placeholder="e.g. Add an endpoint that lists studios below their revenue target this month" required></textarea>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <input class="input" id="engFilename" placeholder="filename, e.g. underperforming_studios.py" style="flex:1;min-width:220px" required>
        <button class="btn primary" type="submit" id="engSubmit"><svg><use href="#i-check"/></svg> Build it</button>
      </div>
    </form>
    <div id="engResult" style="margin-top:10px;display:none"></div>`;
  c.append(box);

  try {
    const health = await api('/api/health');
    const list = box.querySelector('#engFeaturesList');
    const mounted = health.agent_features_mounted || [];
    list.innerHTML = mounted.length
      ? `<div class="hint">Already built: ${mounted.map(m => `<code>${m}</code>`).join(', ')}</div>`
      : `<div class="hint">Nothing built yet. Try the form below.</div>`;
  } catch { /* health check is best-effort here */ }

  box.querySelector('#engForm').onsubmit = async e => {
    e.preventDefault();
    const instruction = box.querySelector('#engInstruction').value.trim();
    const filename = box.querySelector('#engFilename').value.trim();
    const btn = box.querySelector('#engSubmit');
    const resultEl = box.querySelector('#engResult');
    btn.disabled = true; btn.innerHTML = 'Writing, testing…';
    resultEl.style.display = 'none';
    try {
      const r = await fetch('/api/agents/engineer', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ instruction, filename }),
      });
      const data = await r.json();
      resultEl.style.display = '';
      if (r.status === 403) {
        resultEl.innerHTML = `<div class="status-line err"><span class="status-dot"></span>Owner role required. Ask whoever set this app up, or run <code>bin/create_owner.py</code> locally.</div>`;
      } else if (data.ok) {
        resultEl.innerHTML = `<div class="status-line ok"><span class="status-dot"></span>Applied and committed (${data.commit}). <b>Restart the server</b> to activate <code>/api/agent_features/...</code>.</div>`;
        box.querySelector('#engInstruction').value = ''; box.querySelector('#engFilename').value = '';
      } else {
        resultEl.innerHTML = `<div class="status-line err"><span class="status-dot"></span>${(data.error || 'Failed').replace(/</g, '&lt;')}</div>
          ${data.test_output ? `<pre style="max-height:160px;overflow:auto;font-size:11px;margin-top:6px;padding:8px;background:var(--surface-2);border-radius:6px">${data.test_output.slice(-800).replace(/</g, '&lt;')}</pre>` : ''}`;
      }
    } catch {
      resultEl.style.display = ''; resultEl.innerHTML = `<div class="status-line err"><span class="status-dot"></span>Request failed.</div>`;
    }
    btn.disabled = false; btn.innerHTML = '<svg><use href="#i-check"/></svg> Build it';
  };
}

PAGES.agents = async (c) => {
  c.innerHTML = '';

  // Loading skeleton
  const skelGrid = el('div', 'grid cols-3');
  for (let i = 0; i < 9; i++) skelGrid.append(agentSkeletonCard());
  c.append(skelGrid);

  let d;
  try { d = await api('/api/agents'); } catch (e) {
    c.innerHTML = '';
    const errCard = card('AI Agents', '', `
      <div style="display:flex;flex-direction:column;align-items:center;gap:var(--s3);padding:var(--s6) var(--s4)">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--bad)" stroke-width="1.5" style="width:32px;height:32px"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h0"/></svg>
        <div style="color:var(--text-dim)">Failed to load agents. ${e.message || ''}</div>
        <button class="btn primary" onclick="location.reload()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg> Retry</button>
      </div>`);
    c.append(errCard);
    return;
  }
  skelGrid.remove(); // clear skeletons

  const s = d.summary;

  const hero = card(); hero.classList.add('hero-card');
  hero.innerHTML = `<div class="hero-mesh"></div>
    <div style="font-size:var(--fs-xl);font-weight:750;letter-spacing:-.02em">Your AI team</div>
    <div style="color:var(--text-dim);margin-top:6px;max-width:640px;line-height:1.6">A workspace of specialized agents that plan, build, analyze and ship. Assign them to projects, chat, and let them collaborate. Each answer is grounded in your real data.</div>`;
  c.append(hero);

  const kg = el('div', 'grid cols-4'); kg.style.marginTop = 'var(--s4)';
  [['Agents', s.total, 'specialized roles'], ['Active now', s.active, 'working'],
   ['Avg workload', s.avg_workload + '%', 'across the team'], ['Deliverables', s.deliverables, 'produced']]
    .forEach(([l, val, sub]) => { const t = card(); t.classList.add('kpi', 'reveal'); t.innerHTML = `<div class="kpi-label">${l}</div><div class="kpi-value tnum" style="font-size:22px">${val}</div><div style="color:var(--text-faint);font-size:11px">${sub}</div>`; kg.append(t); });
  c.append(kg);

  await renderEngineeringLoop(c);

  // category filter
  const cats = ['All', ...d.categories];
  let activeCat = 'All';
  const chips = el('div'); chips.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;margin-top:var(--s4)';
  const grid = el('div', 'grid cols-3'); grid.style.marginTop = 'var(--s4)';
  const draw = () => {
    grid.innerHTML = '';
    const sorted = [...d.agents].sort((a, b) => a.id === 'orch' ? -1 : b.id === 'orch' ? 1 : 0);
    sorted.filter(a => activeCat === 'All' || a.cat === activeCat).forEach(a => grid.append(agentCard(a)));
  };
  cats.forEach(cat => {
    const ch = el('div', 'chip', cat); if (cat === 'All') ch.style.borderColor = 'var(--accent)';
    ch.onclick = () => { activeCat = cat; $$('.chip', chips).forEach(x => x.style.borderColor = 'var(--border)'); ch.style.borderColor = 'var(--accent)'; draw(); };
    chips.append(ch);
  });
  c.append(chips, grid);
  draw();

  // ---- Activity Trail ----
  const actCard = card('Agent Activity', 'recent actions across the team');
  actCard.style.marginTop = 'var(--s4)';
  const actBody = el('div', 'act-trail');
  actCard.append(actBody);
  c.append(actCard);

  // fetch activity
  try {
    const act = await api('/api/agents/activity');
    const items = (act.activity || []).slice(0, 15);
    if (!items.length) {
      actBody.innerHTML = '<div class="empty" style="padding:var(--s4)">No activity yet.</div>';
    } else {
      items.forEach(item => {
        const ts = item.ts ? timeAgo(item.ts) : '';
        const kindIcon = { task: '📋', project: '🚀', deliverable: '📦', review: '🔍', collaboration: '🤝' }[item.kind] || '•';
        const t = el('div', 'act-item');
        t.innerHTML = `<span class="act-icon">${kindIcon}</span><span class="act-msg">${item.message}</span><span class="act-ts">${ts}</span>`;
        actBody.append(t);
      });
    }
  } catch {
    actBody.innerHTML = '<div class="empty" style="padding:var(--s4);color:var(--text-faint)">Activity feed unavailable.</div>';
  }
};

function agentCard(a) {
  const k = card(); k.classList.add('agent-card');
  const isOrch = a.id === 'orch';
  if (isOrch) k.style.borderColor = 'var(--accent)';
  k.innerHTML = `
    <div class="agent-top">
      <div class="agent-avatar">${a.init}<span class="agent-dot" style="background:${STATUS_COLOR[a.status]}"></span></div>
      <div style="flex:1;min-width:0">
        <div class="agent-role">${a.role}${isOrch ? '<span class="pill" style="margin-left:6px;font-size:9px;background:var(--accent-glow);color:var(--accent)">v2</span>' : ''}</div>
        <div class="agent-exp">${a.expertise}</div>
      </div>
    </div>
    <div class="agent-skills">${a.skills.slice(0, 4).map(s => `<span class="skill">${s}</span>`).join('')}</div>
    <div class="agent-load"><div class="agent-load-label"><span>Workload</span><span>${a.workload}%</span></div>
      <div class="agent-load-bar"><div style="width:${a.workload}%;background:${a.workload > 80 ? 'var(--bad)' : a.workload > 60 ? 'var(--warn)' : 'var(--good)'}"></div></div></div>
    <div class="agent-metrics">
      <div><b>${a.tasks}</b><span>tasks</span></div><div><b>${a.deliverables}</b><span>deliverables</span></div><div><b>${a.rating}</b><span>rating</span></div>
    </div>
    <div class="agent-actions">
      <button class="btn primary" data-chat="${a.id}"><svg><use href="#i-ai"/></svg>Chat</button>
      <button class="btn" data-detail="${a.id}">Details</button>
    </div>`;
  k.querySelector('[data-chat]').onclick = (e) => { e.stopPropagation(); startAgentChat(a); };
  k.querySelector('[data-detail]').onclick = (e) => { e.stopPropagation(); openAgentDetail(a); };
  k.onclick = () => openAgentDetail(a);
  return k;
}

function openAgentDetail(a) {
  $('#scrim').classList.add('open');
  const m = $('#agentModal'); m.classList.add('open');
  m.innerHTML = `
    <div class="modal-head">
      <div class="agent-avatar" style="width:44px;height:44px;font-size:16px">${a.init}<span class="agent-dot" style="background:${STATUS_COLOR[a.status]}"></span></div>
      <div><div style="font-weight:700;font-size:16px">${a.role}</div><div class="page-sub">${a.cat} · ${a.status}</div></div>
      <button class="icon-btn" id="agentClose" aria-label="Close"><svg><use href="#i-close"/></svg></button>
    </div>
    <div class="modal-body">
      <div style="color:var(--text-dim);line-height:1.6">${a.expertise[0].toUpperCase() + a.expertise.slice(1)}.</div>
      <div class="field"><label>Capabilities</label><div class="agent-skills">${a.skills.map(s => `<span class="skill">${s}</span>`).join('')}</div></div>
      <div class="grid cols-3" style="gap:10px">
        ${[['Workload', a.workload + '%'], ['Open tasks', a.tasks], ['Rating', a.rating]].map(([l, val]) => `<div class="card" style="padding:12px"><div class="kpi-value tnum" style="font-size:20px">${val}</div><div style="font-size:11px;color:var(--text-faint)">${l}</div></div>`).join('')}
      </div>
      <div class="field"><label>Actions</label>
        <div class="agent-action-grid">
          ${['Chat', 'Assign Task', 'Invite to Project', 'Create Deliverable', 'Review Work', 'Collaborate'].map(x => `<button class="btn" data-act="${x}">${x}</button>`).join('')}
        </div>
      </div>
    </div>`;
  $('#agentClose').onclick = closeAgentModal;
  $$('[data-act]', m).forEach(b => b.onclick = () => {
    switch (b.dataset.act) {
      case 'Chat': closeAgentModal(); startAgentChat(a); break;
      case 'Assign Task': showTaskForm(a); break;
      case 'Invite to Project': showProjectForm(a); break;
      case 'Create Deliverable': showDeliverableForm(a); break;
      case 'Review Work': showReviewPanel(a); break;
      case 'Collaborate': showCollabForm(a); break;
    }
  });
}

// ---- Coordinator Result Renderer -----------------------------------------

function renderCoordResult(container, d) {
  const agents = d.agents || [];
  const chips = agents.map(a =>
    `<span class="pill" style="background:var(--accent-glow);color:var(--accent);font-size:10px;padding:3px 10px">
       ${a.init} · ${a.role}
     </span>`
  ).join('');
  const fanOutLabel = agents.length > 1
    ? `<span style="font-size:11px;color:var(--text-faint)">Fan-out to ${agents.length} agents</span>`
    : '';

  let html = `
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px">
      ${chips}
      ${fanOutLabel}
    </div>
    <div class="coord-synthesis" style="background:var(--surface-2);border-radius:10px;padding:16px;border:1px solid var(--border);line-height:1.7;font-size:13px">
      ${mdInline(d.synthesis)}
    </div>`;

  // Per-agent contribution detail
  if (agents.length > 1) {
    html += `<div style="margin-top:12px;display:flex;flex-direction:column;gap:8px">`;
    agents.forEach(a => {
      const resp = a.response || '';
      const truncated = resp.length > 300 ? resp.slice(0, 300) + '…' : resp;
      html += `
        <details style="background:var(--surface-1);border-radius:8px;border:1px solid var(--border);padding:10px;font-size:12px">
          <summary style="cursor:pointer;font-weight:600;color:var(--text)">${a.init} · ${a.role}</summary>
          <div style="margin-top:8px;color:var(--text-dim);line-height:1.6">${mdInline(truncated)}</div>
        </details>`;
    });
    html += `</div>`;
  }

  // Data chart if present
  if (d.chart) {
    const chartBox = el('div', 'chart'); chartBox.style.cssText = 'height:280px;margin-top:12px';
    container.innerHTML = html;
    container.append(chartBox);
    chart(chartBox, d.chart);
    return;
  }

  container.innerHTML = html;
}

// ---- Agent Action Dialogs ------------------------------------------------

function showTaskForm(a) {
  const m = showOverlay(`Assign Task to ${a.role}`, `
    <div class="field"><label>Title</label><input id="taskTitle" class="inp" placeholder="e.g. Analyze Q3 conversion dip" autofocus></div>
    <div class="field"><label>Description</label><textarea id="taskDesc" class="inp" rows="3" placeholder="Describe the task…"></textarea></div>
    <div class="grid cols-2" style="gap:10px">
      <div class="field"><label>Priority</label><select id="taskPrio" class="inp"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option></select></div>
      <div class="field"><label>Project (optional)</label><select id="taskProj" class="inp"><option value="">— None —</option></select></div>
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:12px">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn primary" id="taskSubmit">Assign</button>
    </div>`);
  // load projects
  fetch('/api/agents/projects').then(r => r.json()).then(d => {
    const sel = m.querySelector('#taskProj');
    d.projects.forEach(p => { const o = document.createElement('option'); o.value = p.id; o.textContent = p.name; sel.append(o); });
  });
  m.querySelector('#taskSubmit').onclick = async () => {
    const title = m.querySelector('#taskTitle').value.trim();
    if (!title) { toast('Title is required'); return; }
    await fetch('/api/agents/tasks', { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        agent_id: a.id, title, description: m.querySelector('#taskDesc').value.trim(),
        priority: m.querySelector('#taskPrio').value, project_id: m.querySelector('#taskProj').value || null,
      })});
    closeModal(); toast(`Task assigned to ${a.role}`); openAgentDetail(a);
  };
}

function showProjectForm(a) {
  // fetch all agents for peer selection
  fetch('/api/agents').then(r => r.json()).then(d => {
    const peers = d.agents.filter(x => x.id !== a.id);
    const m = showOverlay(`Invite ${a.role} to a Project`, `
      <div class="field"><label>Project name</label><input id="projName" class="inp" placeholder="e.g. Q4 Growth Initiative" autofocus></div>
      <div class="field"><label>Goal</label><input id="projGoal" class="inp" placeholder="e.g. Improve member retention by 20%"></div>
      <div class="field"><label>Add team members</label>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px" id="projPeers">
          ${peers.map(p => `<label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px;padding:4px 8px;background:var(--surface-2);border-radius:6px;border:1px solid var(--border)">
            <input type="checkbox" value="${p.id}"> ${p.role}</label>`).join('')}
        </div>
      </div>
      <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:12px">
        <button class="btn" onclick="closeModal()">Cancel</button>
        <button class="btn primary" id="projSubmit">Create & Invite</button>
      </div>`);
    m.querySelector('#projSubmit').onclick = async () => {
      const name = m.querySelector('#projName').value.trim();
      const goal = m.querySelector('#projGoal').value.trim();
      if (!name || !goal) { toast('Name and goal required'); return; }
      const agent_ids = [a.id];
      m.querySelectorAll('#projPeers input:checked').forEach(cb => agent_ids.push(cb.value));
      await fetch('/api/agents/projects', { method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ name, goal, agent_ids })});
      closeModal(); toast(`Project "${name}" created with ${a.role}`);
    };
  });
}

function showDeliverableForm(a) {
  const types = ['Code', 'Dashboard', 'Design', 'Documentation', 'Report', 'Test Suite'];
  const m = showOverlay(`Create Deliverable: ${a.role}`, `
    <div class="field"><label>Title</label><input id="delTitle" class="inp" placeholder="e.g. Conversion dashboard v2" autofocus></div>
    <div class="field"><label>Type</label><select id="delType" class="inp">${types.map(t => `<option>${t}</option>`).join('')}</select></div>
    <div class="field"><label>Project (optional)</label><select id="delProj" class="inp"><option value="">— None —</option></select></div>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:12px">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn primary" id="delSubmit">Create</button>
    </div>`);
  fetch('/api/agents/projects').then(r => r.json()).then(d => {
    const sel = m.querySelector('#delProj');
    d.projects.forEach(p => { const o = document.createElement('option'); o.value = p.id; o.textContent = p.name; sel.append(o); });
  });
  m.querySelector('#delSubmit').onclick = async () => {
    const title = m.querySelector('#delTitle').value.trim();
    if (!title) { toast('Title is required'); return; }
    await fetch('/api/agents/deliverables', { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        title, type: m.querySelector('#delType').value,
        agent_id: a.id, project_id: m.querySelector('#delProj').value || null,
      })});
    closeModal(); toast(`Deliverable "${title}" created`); openAgentDetail(a);
  };
}

function showReviewPanel(a) {
  const m = showOverlay(`Review Queue: ${a.role}`, '<div id="reviewBody" style="min-height:100px"><div class="loading">Loading reviews…</div></div>');
  const body = m.querySelector('#reviewBody');
  fetch('/api/agents/reviews?agent_id=' + a.id).then(r => r.json()).then(d => {
    if (!d.reviews || !d.reviews.length) {
      body.innerHTML = '<div class="empty" style="padding:40px">No pending reviews for this agent.</div>';
      return;
    }
    body.innerHTML = d.reviews.map(r => `
      <div style="padding:14px;background:var(--surface-2);border-radius:9px;border:1px solid var(--border);margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;align-items:start">
          <div><strong>${r.title}</strong></div>
          <span class="pill ${r.priority}">${r.priority}</span>
        </div>
        <div style="font-size:13px;color:var(--text-dim);margin:6px 0">${r.item}</div>
        <div style="display:flex;gap:8px;margin-top:8px">
          <button class="btn primary small" data-rv="${r.id}" data-action="approve">✓ Approve</button>
          <button class="btn small" data-rv="${r.id}" data-action="changes">↻ Request Changes</button>
        </div>
        <div class="rv-feedback" id="rvf-${r.id}" style="margin-top:8px;display:none">
          <textarea class="inp" rows="2" placeholder="Feedback (optional)…" style="margin-bottom:6px"></textarea>
          <button class="btn small" data-rv="${r.id}" data-action="send">Send</button>
        </div>
      </div>`).join('');
    body.querySelectorAll('[data-action="approve"], [data-action="changes"]').forEach(btn => {
      btn.onclick = () => {
        const rvId = btn.dataset.rv;
        if (btn.dataset.action === 'changes') {
          body.querySelector('#rvf-' + rvId).style.display = 'block';
        } else {
          approveReview(rvId, 'approve', '', body, a);
        }
      };
    });
    body.querySelectorAll('[data-action="send"]').forEach(btn => {
      btn.onclick = () => {
        const rvId = btn.dataset.rv;
        const fb = body.querySelector('#rvf-' + rvId + ' textarea');
        approveReview(rvId, 'changes', fb.value, body, a);
      };
    });
  });
}

async function approveReview(rvId, action, comment, body, a) {
  await fetch('/api/agents/reviews/' + rvId, { method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ action, comment }) });
  toast(`Review ${action === 'approve' ? 'approved' : 'feedback sent'}`);
  showReviewPanel(a); // refresh
}

function showCollabForm(a) {
  fetch('/api/agents').then(r => r.json()).then(d => {
    const peers = d.agents.filter(x => x.id !== a.id);
    const m = showOverlay(`Collaborate: ${a.role}`, `
      <div class="field"><label>With</label>
        <select id="collabPeer" class="inp">
          ${peers.map(p => `<option value="${p.id}">${p.role}</option>`).join('')}
        </select>
      </div>
      <div class="field"><label>Goal</label>
        <textarea id="collabGoal" class="inp" rows="3" placeholder="e.g. Design and implement the new member onboarding flow together" autofocus></textarea>
      </div>
      <div style="color:var(--text-dim);font-size:12px;background:var(--surface-2);padding:10px;border-radius:8px;border:1px solid var(--border)">
        <strong>How collaboration works:</strong> The lead agent coordinates while the peer contributes to their area of expertise. Activity is logged and visible on both agents' profiles.
      </div>
      <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:12px">
        <button class="btn" onclick="closeModal()">Cancel</button>
        <button class="btn primary" id="collabSubmit">Start Collaboration</button>
      </div>`);
    m.querySelector('#collabSubmit').onclick = async () => {
      const peer = m.querySelector('#collabPeer').value;
      const goal = m.querySelector('#collabGoal').value.trim();
      if (!goal) { toast('Describe the collaboration goal'); return; }
      await fetch('/api/agents/collaborations', { method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ lead_id: a.id, peer_id: peer, goal })});
      closeModal(); toast(`Collaboration started: ${a.role} ↔ ...`);
      openAgentDetail(a);
    };
  });
}

// ---- Generic modal overlay ------------------------------------------------
function showOverlay(title, bodyHtml) {
  // close any open agent modal first
  const am = $('#agentModal'); if (am) am.classList.remove('open');
  const scrim = $('#scrim'); scrim.classList.add('open');
  let m = $('#actionModal');
  if (!m) {
    m = el('div'); m.id = 'actionModal'; m.className = 'modal';
    document.body.append(m);
  }
  m.classList.add('open');
  m.innerHTML = `<div class="modal-head">
    <div style="font-weight:700;font-size:16px">${title}</div>
    <button class="icon-btn" onclick="closeModal()" aria-label="Close"><svg><use href="#i-close"/></svg></button>
  </div>
  <div class="modal-body">${bodyHtml}</div>`;
  return m;
}

function closeModal() {
  const m = $('#actionModal'); if (m) m.classList.remove('open');
  const am = $('#agentModal'); if (am) am.classList.remove('open');
  $('#scrim').classList.remove('open');
}
function closeAgentModal() {
  $('#scrim').classList.remove('open');
  $('#agentModal').classList.remove('open');
  const am = $('#actionModal'); if (am) am.classList.remove('open');
}

function startAgentChat(a) {
  state.activeAgent = a.id;
  closeAgentModal();
  // close side-panel chat if open
  $('#chatPanel').classList.remove('open');
  $('#fab').style.display = '';

  // create or reuse agent chat modal
  let modal = $('#agentChatModal');
  if (!modal) {
    modal = el('div'); modal.id = 'agentChatModal'; modal.className = 'agent-chat-modal';
    modal.innerHTML = `
      <div class="agent-chat-head">
        <div class="agent-avatar" id="achatAvatar">DA<span class="agent-dot"></span></div>
        <div class="agent-chat-head-info">
          <div class="name" id="achatName">Data Analyst</div>
          <div class="sub" id="achatSub">Ask anything, answers grounded in real data</div>
        </div>
        <button class="agent-chat-close" id="achatClose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
      </div>
      <div class="agent-chat-body" id="achatBody"></div>
      <div class="agent-chat-input">
        <form class="chat-form" id="achatForm">
          <textarea id="achatText" rows="1" placeholder="Ask your agent…" autofocus></textarea>
          <button class="send-btn" id="achatSend" type="submit"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg></button>
        </form>
      </div>`;
    document.body.append(modal);
  }

  // set agent identity
  const dot = modal.querySelector('#achatAvatar .agent-dot');
  modal.querySelector('#achatAvatar').childNodes[0].textContent = a.init;
  if (dot) dot.style.background = STATUS_COLOR[a.status] || 'var(--text-faint)';
  modal.querySelector('#achatName').textContent = a.role;
  modal.querySelector('#achatSub').textContent = `${a.cat} · ${state.llm && state.llm.enabled ? state.llm.model : 'built-in engine'}`;

  // wire close
  const closeBtn = modal.querySelector('#achatClose');
  closeBtn.onclick = closeAgentChat;

  // wire form
  const ta = modal.querySelector('#achatText');
  ta.oninput = () => { ta.style.height = 'auto'; ta.style.height = Math.min(100, ta.scrollHeight) + 'px'; };
  ta.onkeydown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); modal.querySelector('#achatForm').requestSubmit(); } };
  modal.querySelector('#achatForm').onsubmit = e => {
    e.preventDefault();
    const q = ta.value.trim();
    if (q) { ta.value = ''; ta.style.height = 'auto'; sendAgentChat(a, q); }
  };
  ta.focus();

  modal.classList.add('open');

  // Welcome message if body is empty
  const body = modal.querySelector('#achatBody');
  if (!body.children.length) {
    const b = addAgentMsg('bot', modal);
    b.innerHTML = mdInline(`Hi! I'm your **${a.role}**. I focus on ${a.expertise}. Ask me anything, I'll ground answers in your real data.`);
    const chips = el('div', 'chips');
    const fps = agentFollowups(a.id);
    fps.forEach(f => { const ch = el('div', 'chip', f); ch.onclick = () => { ta.value = f; modal.querySelector('#achatForm').requestSubmit(); }; chips.append(ch); });
    b.append(chips);
  }
}

function closeAgentChat() {
  const modal = $('#agentChatModal');
  if (modal && modal.classList.contains('open')) {
    modal.classList.remove('open');
  }
  $('#fab').style.display = '';
}

function addAgentMsg(role, modal) {
  const m = el('div', `msg ${role}`);
  const b = el('div', 'bubble');
  m.append(b);
  const body = modal ? modal.querySelector('#achatBody') : $('#achatBody');
  body.append(m); body.scrollTop = 1e6;
  return b;
}

async function sendAgentChat(a, q) {
  const modal = $('#agentChatModal');
  if (!modal) return;

  // user message
  addAgentMsg('user', modal).textContent = q;

  // typing indicator
  const typing = addAgentMsg('bot', modal);
  typing.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';

  try {
    const res = await fetch('/api/agents/chat/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: a.id, message: q }),
    });
    if (!res.ok) { typing.closest('.msg')?.remove(); addAgentMsg('bot', modal).textContent = 'Error reaching agent.'; return; }

    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '', narration = '', chartNode = null, answer = null;
    typing.closest('.msg')?.remove();
    const b = addAgentMsg('bot', modal);

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split('\n\n'); buf = parts.pop();
      for (const part of parts) {
        const ev = part.match(/event: (\w+)/)?.[1];
        const dataLine = part.match(/data: (.*)/s)?.[1];
        if (!ev || !dataLine) continue;
        try {
          const payload = JSON.parse(dataLine);
          if (ev === 'answer') {
            answer = payload;
            if (payload.table) b.append(renderMiniTable(payload.table));
            if (payload.chart) chartNode = el('div', 'msg-chart');
          } else if (ev === 'token') {
            narration += payload.t;
            b.innerHTML = mdInline(narration);
          } else if (ev === 'done') {
            if (chartNode && answer?.chart) { b.append(chartNode); chart(chartNode, answer.chart); }
            if (answer?.provenance) b.append(el('div', 'prov', `ƒ ${answer.provenance}`));
            if (answer?.followups?.length) {
              const chips = el('div', 'chips');
              answer.followups.forEach(f => { const ch = el('div', 'chip', f);
                ch.onclick = () => { const inp = modal.querySelector('#achatText'); inp.value = f; modal.querySelector('#achatForm').requestSubmit(); };
                chips.append(ch); });
              b.append(chips);
            }
          }
        } catch {}
      }
      modal.querySelector('#achatBody').scrollTop = 1e6;
    }
  } catch {
    typing.closest('.msg')?.remove();
    addAgentMsg('bot', modal).textContent = 'Connection error. Try again.';
  }
}

function agentFollowups(agentId) {
  const map = {
    orch: ['Team capacity overview', 'What projects are active?', 'Route a question to the right agent'],
    da: ['Revenue by channel for Q3', 'Which studios miss target?', 'Kenapa CR Crestline turun?'],
    gm: ['Funnel conversion rate trend', 'CAC per channel last month', 'Retention by studio'],
    ml: ['Forecast next 3 months', 'Any anomalies this week?', 'Revenue prediction by city'],
    pm: ['Project status summary', 'What tasks are overdue?', 'Team workload overview'],
    proj: ['Timeline for active projects', 'Any blocked tasks?', 'Resource allocation'],
    de: ['Data pipeline status', 'Table freshness report', 'Schema changes'],
    ae: ['Data quality metrics', 'Mart lineage', 'Metric definitions'],
    fe: ['UI component library', 'Accessibility audit', 'Performance metrics'],
    be: ['API performance', 'Security review', 'Database health'],
    fs: ['API endpoint status', 'Deployment pipeline', 'Tech stack overview'],
    qa: ['Test coverage report', 'Recent bugs', 'Regression status'],
    uxd: ['User flow analysis', 'Wireframe review', 'Interaction design'],
    uid: ['Design system health', 'Component usage', 'Visual consistency'],
    mkt: ['Campaign performance', 'Channel ROI', 'GTM strategy'],
    cont: ['Content performance', 'SEO ranking', 'Editorial calendar'],
    uxr: ['Recent user studies', 'Usability findings', 'Research backlog'],
    ops: ['Process efficiency', 'SLA compliance', 'Capacity planning'],
    csm: ['Member retention rate', 'Onboarding completion', 'Health scores'],
    ba: ['Requirements status', 'Process mapping', 'Gap analysis'],
  };
  return map[agentId] || ['What data do you have?', 'How can you help me?', 'Tell me about your expertise'];
}

// ---------- filters / export ----------
function applyFilter(f) {
  state.filters = { ...state.filters };
  ['city', 'channel', 'studio'].forEach(k => { if (f[k] != null) state.filters[k] = f[k]; });
  $$('#filterBar select').forEach(s => { const k = s.dataset.filter; if (f[k] != null) s.value = f[k]; });
  toast('Filter applied: ' + Object.values(f).join(', '));
}
function exportCSV(name, rows) {
  if (!rows || !rows.length) return;
  const cols = Object.keys(rows[0]);
  const csv = [cols.join(','), ...rows.map(r => cols.map(c => JSON.stringify(r[c] ?? '')).join(','))].join('\n');
  const a = el('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = `fitflow_${name}.csv`; a.click();
  toast('Exported ' + name + '.csv');
}

// ---------- chrome wiring ----------
function wireChrome() {
  $('#toggleSidebar').onclick = () => {
    if (matchMedia('(max-width:860px)').matches) $('#sidebar').classList.toggle('show');
    else $('#app').classList.toggle('collapsed');
  };
  $('#cmdkOpen').onclick = openCmdk;
  $('#scrim').onclick = () => { closeCmdk(); closeModal(); closeAgentChat(); };
  $('#themeToggle').onclick = () => applyTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light');
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openCmdk(); }
    if (e.key === 'Escape') { closeCmdk(); closeModal(); closeAgentChat(); $('#chatPanel').classList.remove('open'); }
  });
}

// ---------- AI settings modal ----------
// Friendly label + one-line hint per provider, shown under the dropdown.
// "key from" names each provider's own site in plain text (not a link) so
// someone unfamiliar with these providers knows where to go get a key.
const PROVIDER_INFO = {
  anthropic:  { label: 'Claude (Anthropic)',        hint: 'key from console.anthropic.com' },
  openai:     { label: 'OpenAI (GPT)',               hint: 'key from platform.openai.com' },
  deepseek:   { label: 'DeepSeek',                   hint: 'key from platform.deepseek.com. Cheap, good default.' },
  kimi:       { label: 'Kimi (Moonshot AI)',         hint: 'key from platform.moonshot.ai' },
  qwen:       { label: 'Qwen (Alibaba Cloud)',       hint: 'key from dashscope.console.aliyun.com' },
  groq:       { label: 'Groq',                       hint: 'key from console.groq.com. Very fast responses.' },
  openrouter: { label: 'OpenRouter',                 hint: 'key from openrouter.ai. One key, many models.' },
  together:   { label: 'Together AI',                hint: 'key from api.together.ai' },
  mistral:    { label: 'Mistral AI',                 hint: 'key from console.mistral.ai' },
  xai:        { label: 'Grok (xAI)',                 hint: 'key from console.x.ai' },
  fireworks:  { label: 'Fireworks AI',                hint: 'key from fireworks.ai' },
  perplexity: { label: 'Perplexity',                  hint: 'key from perplexity.ai/settings/api' },
  gemini:     { label: 'Gemini (Google)',             hint: 'key from aistudio.google.com' },
  ollama:     { label: 'Ollama (runs on your own machine)', hint: 'free, no key needed, but must be running locally' },
};
const PROVIDER_ORDER = ['anthropic', 'openai', 'deepseek', 'kimi', 'qwen', 'groq', 'openrouter',
  'together', 'mistral', 'xai', 'fireworks', 'perplexity', 'gemini', 'ollama'];

function _fillProviderSelect(sel, hintEl) {
  sel.innerHTML = PROVIDER_ORDER.map(id => `<option value="${id}">${PROVIDER_INFO[id].label}</option>`).join('');
  const paint = () => { hintEl.textContent = PROVIDER_INFO[sel.value].hint; };
  sel.onchange = paint;
  paint();
}

function initSettings() {
  _fillProviderSelect($('#aiProvider'), $('#aiProviderHint'));
  $('#aiProvider').value = 'deepseek'; $('#aiProviderHint').textContent = PROVIDER_INFO.deepseek.hint;
  _fillProviderSelect($('#aiProviderEng'), $('#aiProviderHintEng'));

  $('#aiSettings').onclick = openModal;
  $('#aiModalClose').onclick = closeAiModal;
  $('#aiSave').onclick = () => saveSettings(false);
  $('#aiSaveEng').onclick = () => saveSettings(true);
  $('#aiDisconnect').onclick = async () => {
    await fetch('/api/settings/llm/clear', { method: 'POST' });
    const data = await (await fetch('/api/settings/llm')).json();
    reflectLLM(data); paintAiStatus(); toast('Switched to built-in engine');
  };
  $('#aiDisconnectEng').onclick = async () => {
    await fetch('/api/settings/llm/engineer/clear', { method: 'POST' });
    const data = await (await fetch('/api/settings/llm')).json();
    reflectLLM(data); paintAiStatus(); toast('Engineering loop will reuse the chat model');
  };
}
function openModal() { $('#scrim').classList.add('open'); $('#aiModal').classList.add('open'); paintAiStatus(); }
function closeAiModal() { $('#scrim').classList.remove('open'); $('#aiModal').classList.remove('open'); }
function paintAiStatus() {
  const l = $('#aiStatusLine'), t = $('#aiStatusText');
  if (state.llm && state.llm.enabled) {
    l.className = 'status-line ok'; t.textContent = `Connected: ${PROVIDER_INFO[state.llm.provider]?.label || state.llm.provider} · ${state.llm.model}`;
  } else {
    l.className = 'status-line off'; t.textContent = 'Using built-in deterministic engine (no key needed)';
  }
  const le = $('#aiStatusLineEng'), te = $('#aiStatusTextEng');
  if (state.llm && state.llm.engineer_override) {
    le.className = 'status-line ok'; te.textContent = `Connected: ${PROVIDER_INFO[state.llm.engineer_provider]?.label || state.llm.engineer_provider} · ${state.llm.engineer_model}`;
  } else {
    le.className = 'status-line off'; te.textContent = 'Using the chat model above';
  }
}
async function saveSettings(forEngineer) {
  const suffix = forEngineer ? 'Eng' : '';
  const key = $('#aiKey' + suffix).value.trim();
  if (!key) { toast('Enter an API key first'); return; }
  const btn = $('#aiSave' + suffix); btn.disabled = true; btn.innerHTML = 'Testing…';
  const url = forEngineer ? '/api/settings/llm/engineer' : '/api/settings/llm';
  try {
    const res = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: $('#aiProvider' + suffix).value,
        api_key: key,
        model: $('#aiModel' + suffix).value.trim() || null,
        test: true,
      }),
    });
    const data = await res.json();
    const statusLine = $('#aiStatusLine' + suffix), statusText = $('#aiStatusText' + suffix);
    if (!res.ok || !data.ok) { statusLine.className = 'status-line err'; statusText.textContent = data.error || 'Connection failed'; }
    else {
      reflectLLM(data); paintAiStatus();
      toast(`Connected to ${PROVIDER_INFO[forEngineer ? data.engineer_provider : data.provider]?.label || 'provider'}`);
      $('#aiKey' + suffix).value = '';
    }
  } catch { toast('Connection failed'); }
  btn.disabled = false; btn.innerHTML = '<svg><use href="#i-check"/></svg> Test & connect';
}

// ---------- chat ----------
function initChat() {
  $('#fab').onclick = () => { state.activeAgent = null; $('#chatMode').textContent = state.llm && state.llm.enabled ? `${state.llm.provider} · ${state.llm.model}` : 'built-in engine (no key)'; $('#chatPanel').classList.add('open'); $('#chatText').focus(); $('#fab').style.display = 'none'; };
  $('#chatClose').onclick = closeChat;
  // click outside to dismiss chat
  document.addEventListener('click', e => {
    const panel = $('#chatPanel'); const fab = $('#fab');
    if (!panel.classList.contains('open')) return;
    if (!panel.contains(e.target) && !fab.contains(e.target)) closeChat();
  }, true);
  // esc to close chat
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && $('#chatPanel').classList.contains('open')) closeChat(); });
  const ta = $('#chatText');
  ta.addEventListener('input', () => { ta.style.height = 'auto'; ta.style.height = Math.min(120, ta.scrollHeight) + 'px'; });
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#chatForm').requestSubmit(); } });
  $('#chatForm').onsubmit = e => { e.preventDefault(); const q = ta.value.trim(); if (q) { ta.value = ''; ta.style.height = 'auto'; sendChat(q); } };
  botSay({ text: `Hi! I'm your **AI Analyst**. Ask me about revenue, members, CAC, ROAS, conversion, forecasts or anomalies · in English or Indonesian.`,
    followups: ['Revenue by channel for Q3', 'Kenapa CR Crestline turun September?', 'Which studios miss target?', 'Forecast next month revenue'] });
}
function closeChat() { $('#chatPanel').classList.remove('open'); $('#fab').style.display = ''; }

// ---------- account dropdown ----------
async function refreshOrgSelect() {
  const sel = $('#orgSelect');
  const current = sessionStorage.getItem('grc-org') || '';
  let orgs = [];
  try { orgs = (await api('/api/orgs')).orgs || []; } catch { /* not logged in yet */ }
  sel.innerHTML = '<option value="">Default (shared demo)</option>' +
    orgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
  sel.value = orgs.some(o => o.id === current) ? current : '';
  if (sel.value !== current) sessionStorage.removeItem('grc-org'); // stale org id, fall back
}

function initAccount() {
  $('#accountUser').textContent = sessionStorage.getItem('grc-user') || 'try';
  $('#accountBtn').onclick = e => { e.stopPropagation(); $('#accountDrop').classList.toggle('open'); refreshOrgSelect(); };
  document.addEventListener('click', e => {
    if (!$('#accountDrop').contains(e.target) && e.target !== $('#accountBtn')) $('#accountDrop').classList.remove('open');
  }, true);
  $('#logoutBtn').onclick = () => { sessionStorage.removeItem('grc-token'); sessionStorage.removeItem('grc-user'); sessionStorage.removeItem('grc-org'); location.reload(); };
  $('#orgSelect').onchange = e => {
    if (e.target.value) sessionStorage.setItem('grc-org', e.target.value);
    else sessionStorage.removeItem('grc-org');
    location.reload(); // simplest way to re-fetch every page's data under the new org
  };
  $('#newOrgBtn').onclick = async () => {
    const name = prompt('New organization name:');
    if (!name) return;
    $('#newOrgBtn').textContent = 'Creating… (~1-2 min)';
    $('#newOrgBtn').disabled = true;
    try {
      const org = await api('/api/orgs', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name }) });
      sessionStorage.setItem('grc-org', org.id);
      location.reload();
    } catch {
      alert('Could not create org.');
      $('#newOrgBtn').textContent = '+ New org';
      $('#newOrgBtn').disabled = false;
    }
  };
  refreshOrgSelect();
}
function addMsg(role) { const m = el('div', `msg ${role}`); const b = el('div', 'bubble'); m.append(b); $('#chatBody').append(m); $('#chatBody').scrollTop = 1e6; return b; }
function botSay(ans) {
  const b = addMsg('bot');
  b.innerHTML = mdInline(ans.text || '');
  if (ans.table) b.append(renderMiniTable(ans.table));
  if (ans.chart) { const cn = el('div', 'msg-chart'); b.append(cn); setTimeout(() => { if (ans.chart.title) { ans.chart.grid = { ...ans.chart.grid, top: Math.max(ans.chart.grid?.top || 38, 56) }; ans.chart.legend = { ...ans.chart.legend, top: 20 }; } chart(cn, ans.chart); }, 30); }
  if (ans.provenance) { const p = el('div', 'prov', `ƒ ${ans.provenance}`); b.append(p); }
  if (ans.sql) {
    const sqlBtn = el('button', 'btn ghost', 'Open in SQL Workspace');
    sqlBtn.style.cssText = 'font-size:10px;padding:4px 10px;margin-top:4px';
    sqlBtn.onclick = () => { state.sqlPrefill = ans.sql; closeChat(); go('sql'); };
    b.append(sqlBtn);
  }
  if (ans.followups && ans.followups.length) {
    const chips = el('div', 'chips');
    ans.followups.forEach(f => { const ch = el('div', 'chip', f); ch.onclick = () => sendChat(f); chips.append(ch); });
    b.append(chips);
  }
  $('#chatBody').scrollTop = 1e6;
}
function renderMiniTable(t) {
  const wrap = el('div', 'msg-table'); const tbl = el('table', 'data');
  tbl.innerHTML = `<thead><tr>${t.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
    <tbody>${t.rows.slice(0, 8).map(r => `<tr>${t.columns.map(c => `<td>${r[c] ?? '–'}</td>`).join('')}</tr>`).join('')}</tbody>`;
  wrap.append(tbl); return wrap;
}
async function sendChat(q) {
  if ($('#fab').style.display === 'none') {} else { $('#chatPanel').classList.add('open'); $('#fab').style.display = 'none'; }
  addMsg('user').textContent = q; $('#chatBody').scrollTop = 1e6;
  const typing = addMsg('bot'); typing.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
  try {
    // try streaming endpoint; fall back to JSON
    const res = await fetch('/api/ask/stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q, agent: state.activeAgent || null }) });
    if (res.status === 429) { typing.closest('.msg').remove(); botSay({ text: '⏳ Rate limit reached · try again in a moment.' }); return; }
    const reader = res.body.getReader(); const dec = new TextDecoder();
    let buf = '', answer = null, narration = '';
    typing.closest('.msg').remove();
    const b = addMsg('bot'); let chartNode = null;
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split('\n\n'); buf = parts.pop();
      for (const part of parts) {
        const ev = part.match(/event: (\w+)/)?.[1]; const dataLine = part.match(/data: (.*)/s)?.[1];
        if (!ev || !dataLine) continue;
        const payload = JSON.parse(dataLine);
        if (ev === 'answer') {
          answer = payload;
          if (payload.table) b.append(renderMiniTable(payload.table));
          if (payload.chart) { chartNode = el('div', 'msg-chart'); }
        } else if (ev === 'token') {
          narration += payload.t; b.innerHTML = mdInline(narration);
          if (answer?.table) b.append(renderMiniTable(answer.table));
        } else if (ev === 'done') {
          if (chartNode) { b.append(chartNode); if (answer?.chart?.title) { answer.chart.grid = { ...answer.chart.grid, top: Math.max(answer.chart.grid?.top || 38, 56) }; answer.chart.legend = { ...answer.chart.legend, top: 20 }; } chart(chartNode, answer.chart); }
          if (answer?.provenance) b.append(el('div', 'prov', `ƒ ${answer.provenance}`));
          if (answer?.sql) {
            const sqlBtn = el('button', 'btn ghost', 'Open in SQL Workspace');
            sqlBtn.style.cssText = 'font-size:10px;padding:4px 10px;margin-top:4px';
            sqlBtn.onclick = () => { state.sqlPrefill = answer.sql; closeChat(); go('sql'); };
            b.append(sqlBtn);
          }
          if (answer?.followups?.length) { const chips = el('div', 'chips'); answer.followups.forEach(f => { const ch = el('div', 'chip', f); ch.onclick = () => sendChat(f); chips.append(ch); }); b.append(chips); }
        }
      }
      $('#chatBody').scrollTop = 1e6;
    }
  } catch (err) {
    typing.closest('.msg')?.remove();
    try { const ans = await (await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q }) })).json(); botSay(ans); }
    catch { botSay({ text: 'Something went wrong reaching the analyst.' }); }
  }
}

// ---------- command palette ----------
let cmdkItems = [], cmdkSel = 0;
function openCmdk() {
  $('#scrim').classList.add('open'); $('#cmdk').classList.add('open');
  const inp = $('#cmdkInput'); inp.value = ''; inp.focus(); buildCmdk('');
  inp.oninput = () => buildCmdk(inp.value);
  inp.onkeydown = e => {
    if (e.key === 'ArrowDown') { cmdkSel = Math.min(cmdkSel + 1, cmdkItems.length - 1); paintCmdk(); e.preventDefault(); }
    if (e.key === 'ArrowUp') { cmdkSel = Math.max(cmdkSel - 1, 0); paintCmdk(); e.preventDefault(); }
    if (e.key === 'Enter') { cmdkItems[cmdkSel]?.run(); }
  };
}
function closeCmdk() { $('#scrim').classList.remove('open'); $('#cmdk').classList.remove('open'); }
function buildCmdk(q) {
  const ql = q.toLowerCase();
  const nav = NAV.map(n => ({ icon: n.icon, label: n.label, tag: 'Page', run: () => { closeCmdk(); go(n.id); } }));
  const asks = ['Revenue by channel for Q3', 'Why did CR drop in Crestline?', 'Which studios miss target?', 'Forecast next month revenue', 'CAC per channel last month']
    .map(a => ({ icon: 'i-ai', label: a, tag: 'Ask AI', run: () => { closeCmdk(); sendChat(a); } }));
  cmdkItems = [...nav, ...asks].filter(i => !ql || i.label.toLowerCase().includes(ql));
  cmdkSel = 0; paintCmdk();
}
function paintCmdk() {
  const list = $('#cmdkList'); list.innerHTML = '';
  cmdkItems.forEach((it, i) => {
    const row = el('div', 'cmdk-row' + (i === cmdkSel ? ' sel' : ''), `<svg><use href="#${it.icon}"/></svg><span>${it.label}</span><span class="tag">${it.tag}</span>`);
    row.onclick = it.run; row.onmouseenter = () => { cmdkSel = i; };
    list.append(row);
  });
  if (!cmdkItems.length) list.append(el('div', 'empty', 'No matches'));
}

// ---------- guided tour ----------
const TOUR = [
  { sel: '[data-tour="kpi"]', title: '1 · Live KPIs', body: 'Every tile is a real aggregate from the warehouse with month-over-month deltas. No hardcoded numbers.' },
  { sel: '[data-tour="insights"]', title: '2 · Auto-Insights', body: 'This feed is generated by an anomaly + target-pace engine. Click any item to jump into a pre-filtered view.' },
  { sel: '[data-tour="anomalystory"]', title: '3 · The story it found', body: "Crestline's lead quality collapses from September · visible here, hidden in blended averages. The AI explains why.", page: 'overview' },
  { sel: '#fab', title: '4 · AI Analyst (no API key)', body: 'Ask in Indonesian or English. Answers carry real numbers, a chart, and the SQL provenance · all from a deterministic engine.' },
  { sel: '[data-tour="lineage"]', title: '5 · Real dbt lineage', body: 'Parsed live from dbt manifest.json · staging → marts. This is the data-engineering proof.', page: 'quality' },
];
let tourIdx = 0;
async function startTour() {
  tourIdx = 0; showTourStep();
}
async function showTourStep() {
  $('#tourLayer')?.remove();
  const step = TOUR[tourIdx]; if (!step) return;
  if (step.page && state.page !== step.page) { go(step.page); await new Promise(r => setTimeout(r, 450)); }
  if (step.sel === '#fab' && $('#fab').style.display === 'none') { $('#chatClose').click(); }
  const target = $(step.sel); if (!target) { tourIdx++; return showTourStep(); }
  const r = target.getBoundingClientRect();
  const layer = el('div', 'tour'); layer.id = 'tourLayer';
  const cardE = el('div', 'tour-card');
  cardE.innerHTML = `<h4>${step.title}</h4><p>${step.body}</p>
    <div class="tour-foot"><div class="tour-dots">${TOUR.map((_, i) => `<i class="${i === tourIdx ? 'on' : ''}"></i>`).join('')}</div>
    <div><button class="btn ghost" id="tourSkip">Skip</button> <button class="btn primary" id="tourNext">${tourIdx === TOUR.length - 1 ? 'Done' : 'Next'}</button></div></div>`;
  layer.append(cardE); document.body.append(layer);
  // position card near target
  let top = r.bottom + 12, left = r.left;
  if (top + 180 > innerHeight) top = Math.max(20, r.top - 190);
  left = Math.min(left, innerWidth - 340);
  cardE.style.top = top + 'px'; cardE.style.left = Math.max(16, left) + 'px';
  // spotlight ring
  target.style.outline = '2px solid var(--accent)'; target.style.outlineOffset = '3px'; target.style.borderRadius = '14px';
  target.scrollIntoView({ block: 'center', behavior: 'smooth' });
  const cleanup = () => { target.style.outline = ''; layer.remove(); };
  $('#tourSkip').onclick = cleanup;
  $('#tourNext').onclick = () => { cleanup(); tourIdx++; if (tourIdx < TOUR.length) showTourStep(); else toast('Tour complete · explore freely!'); };
}
