const $ = (id) => document.getElementById(id);
let chart = null;
let lastAnswer = '';
let branchCatalog = null;

const branchCatalogReady = fetch('/data/branch_aliases.json', { cache: 'no-store' })
  .then((r) => (r.ok ? r.json() : null))
  .then((x) => {
    branchCatalog = x;
    return x;
  })
  .catch(() => null);

const PROFILE_KEY = 'tvai_profiles_v2';
const branches = { Hợi: [4, 4], Tý: [4, 3], Sửu: [4, 2], Dần: [4, 1], Mão: [3, 1], Thìn: [2, 1], Tỵ: [1, 1], Ngọ: [1, 2], Mùi: [1, 3], Thân: [1, 4], Dậu: [2, 4], Tuất: [3, 4] };
const order = ['Hợi', 'Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất'];
const TRIPLE = {
  Hợi: ['Hợi', 'Mão', 'Mùi'], Mão: ['Hợi', 'Mão', 'Mùi'], Mùi: ['Hợi', 'Mão', 'Mùi'],
  Dần: ['Dần', 'Ngọ', 'Tuất'], Ngọ: ['Dần', 'Ngọ', 'Tuất'], Tuất: ['Dần', 'Ngọ', 'Tuất'],
  Tỵ: ['Tỵ', 'Dậu', 'Sửu'], Dậu: ['Tỵ', 'Dậu', 'Sửu'], Sửu: ['Tỵ', 'Dậu', 'Sửu'],
  Thân: ['Thân', 'Tý', 'Thìn'], Tý: ['Thân', 'Tý', 'Thìn'], Thìn: ['Thân', 'Tý', 'Thìn'],
};
const OPP = { Tý: 'Ngọ', Ngọ: 'Tý', Sửu: 'Mùi', Mùi: 'Sửu', Dần: 'Thân', Thân: 'Dần', Mão: 'Dậu', Dậu: 'Mão', Thìn: 'Tuất', Tuất: 'Thìn', Tỵ: 'Hợi', Hợi: 'Tỵ' };
const NHI = { Tý: 'Sửu', Sửu: 'Tý', Dần: 'Hợi', Hợi: 'Dần', Mão: 'Tuất', Tuất: 'Mão', Thìn: 'Dậu', Dậu: 'Thìn', Tỵ: 'Thân', Thân: 'Tỵ', Ngọ: 'Mùi', Mùi: 'Ngọ' };
const starH = {
  'Tử vi': 'tho', 'Liêm trinh': 'hoa', 'Thiên đồng': 'thuy', 'Vũ khúc': 'kim', 'Thái Dương': 'hoa',
  'Thiên cơ': 'moc', 'Thiên phủ': 'tho', 'Thái âm': 'thuy', 'Tham lang': 'thuy', 'Cự môn': 'thuy',
  'Thiên tướng': 'thuy', 'Thiên lương': 'tho', 'Thất sát': 'kim', 'Phá quân': 'thuy', 'Hóa khoa': 'kim',
  'Hóa quyền': 'hoa', 'Hóa lộc': 'moc', 'Hóa kỵ': 'thuy', 'Kình dương': 'kim', 'Đà la': 'kim',
  'Địa không': 'hoa', 'Địa kiếp': 'hoa', 'Linh tinh': 'hoa', 'Hỏa tinh': 'hoa', 'Văn xương': 'kim',
  'Văn Khúc': 'thuy', 'Thiên khôi': 'hoa', 'Thiên việt': 'hoa', 'Tả phù': 'tho', 'Hữu bật': 'thuy',
  'Quốc ấn': 'tho', 'Thiên hình': 'hoa',
};
const MAIN_STAR_IDS = new Set(Array.from({ length: 14 }, (_, i) => i + 1));
const TRANG_SINH_IDS = new Set(Array.from({ length: 12 }, (_, i) => i + 39));

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m] || m));
const norm = (s) => String(s ?? '').trim().toLowerCase().replace(/\s+/g, ' ');
const asList = (v) => (Array.isArray(v) ? v : (v && typeof v === 'object' ? Object.values(v) : []));
const starId = (s) => {
  const n = Number(s?.id ?? s?.saoID);
  return Number.isFinite(n) ? n : null;
};
const starName = (s) => s?.ten || s?.name || s?.saoTen || s?.sao || s || '';
const isTrangSinh = (s) => TRANG_SINH_IDS.has(starId(s)) || Boolean(s?.vong_trang_sinh || s?.vongTrangSinh);

function branchOf(p) {
  const key = String(p?.branch_key || '').trim().toLowerCase();
  if (key && branchCatalog?.branches?.[key]?.label) return branchCatalog.branches[key].label;
  const x = String(p?.dia_chi ?? p?.chi ?? p?.branch ?? '').trim();
  if (!x) return '';
  const folded = x.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/đ/g, 'd');
  const match = Object.entries(branchCatalog?.branches || {}).find(([_, v]) =>
    v.aliases.some((a) => {
      const alias = String(a).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/đ/g, 'd');
      return folded === alias;
    }),
  );
  return match?.[1]?.label || order.find((b) => x === b || x.includes(b)) || '';
}

function palaceByName(n) {
  return Object.values(chart?.['12_cung'] || {}).find((p) => norm(p?.cung) === norm(n));
}

function supportStars(p) {
  const direct = asList(p?.phu_tinh || p?.phuTinh);
  if (direct.length) return direct;
  const all = asList(p?.sao || p?.stars || p?.all_stars);
  return all.filter((s) => !MAIN_STAR_IDS.has(starId(s)) && !isTrangSinh(s) && Number(s?.loai ?? s?.saoLoai) !== 1);
}

function allStarsInPalace(p) {
  const raw = asList(p?.sao || p?.stars || p?.all_stars);
  if (raw.length) return raw;
  return [
    ...asList(p?.chinh_tinh),
    ...supportStars(p),
    ...asList(p?.vong_trang_sinh_data || p?.vongTrangSinhData),
  ].filter(Boolean);
}

function totalStars(palaces) {
  return palaces.reduce((sum, p) => sum + allStarsInPalace(p).length, 0);
}

function trangSinhName(p) {
  const direct = p?.trang_sinh || p?.vong_trang_sinh;
  if (direct) return direct;
  const data = asList(p?.vong_trang_sinh_data || p?.vongTrangSinhData);
  if (data.length) return starName(data[0]);
  const found = asList(p?.sao || p?.stars || p?.all_stars).find(isTrangSinh);
  return found ? starName(found) : '';
}

function starChip(x, main = false) {
  const n = starName(x);
  const nh = starH[n] || starH[Object.keys(starH).find((k) => norm(k) === norm(n))] || '';
  return `<span class="chip ${main ? 'main' : ''} ${nh ? `nh-${nh}` : ''}">${esc(n)}</span>`;
}

function stars(list, main = false) {
  return asList(list).map((x) => starChip(x, main)).join('') || '<span class="meta">—</span>';
}

function currentViewYear() {
  const value = Number($('viewYear')?.value);
  return Number.isInteger(value) && value >= 1800 && value <= 2200 ? value : new Date().getFullYear();
}

function profilePayload() {
  return {
    day: +$('day').value || 1,
    month: +$('month').value || 1,
    year: +$('year').value || 1996,
    hour: $('hour').value,
    gender: $('gender').value,
    calendar: $('calendar').value,
    tz: +$('tz').value || 7,
    name: $('name').value || '',
    viewYear: currentViewYear(),
  };
}

function profileSignature(p) {
  return [p.name.trim().toLowerCase() || '—', p.day, p.month, p.year, p.hour, p.gender, p.calendar, p.tz].join('|');
}

function hashId(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return `TV-${(h >>> 0).toString(16).toUpperCase().padStart(8, '0')}`;
}

function profiles() {
  try {
    return JSON.parse(localStorage.getItem(PROFILE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveProfiles(list) {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(list));
}

function refreshProfiles(activeId = '') {
  const sel = $('profileSelect');
  const list = profiles();
  sel.innerHTML = '<option value="">Hồ sơ mới</option>' + list.map((p) => `<option value="${esc(p.id)}">${esc(p.name || 'Không tên')} · ${esc(p.birth)}</option>`).join('');
  sel.value = activeId || '';
  const p = list.find((x) => x.id === activeId);
  $('profileId').textContent = `ID: ${p?.id || '—'}`;
}

function upsertProfile() {
  const p = profilePayload();
  const id = hashId(profileSignature(p));
  const list = profiles();
  const item = {
    id,
    name: p.name.trim() || 'Không tên',
    birth: `${String(p.day).padStart(2, '0')}/${String(p.month).padStart(2, '0')}/${p.year}`,
    ...p,
  };
  const i = list.findIndex((x) => x.id === id);
  if (i >= 0) list[i] = { ...list[i], ...item };
  else list.unshift(item);
  saveProfiles(list);
  refreshProfiles(id);
}

function loadProfile(id) {
  const p = profiles().find((x) => x.id === id);
  if (!p) return;
  ['day', 'month', 'year', 'hour', 'gender', 'calendar', 'tz', 'name'].forEach((k) => {
    if (p[k] != null) $(k).value = p[k];
  });
  if (p.viewYear != null && $('viewYear')) $('viewYear').value = p.viewYear;
  $('profileId').textContent = `ID: ${p.id}`;
}

function relationData(p) {
  const b = branchOf(p);
  if (!b) return null;
  const arr = Object.values(chart?.['12_cung'] || {});
  const by = new Map(arr.map((x) => [branchOf(x), x]));
  const tri = TRIPLE[b] || [];
  const i = order.indexOf(b);
  const giap = [order[(i + 11 + 12) % 12], order[(i + 1) % 12]];
  return {
    base: { branch: b, palace: p },
    tamhop: tri.filter((x) => x !== b).map((x) => by.get(x)).filter(Boolean),
    xung: [by.get(OPP[b])].filter(Boolean),
    nhihop: [by.get(NHI[b])].filter(Boolean),
    giap: giap.map((x) => by.get(x)).filter(Boolean),
  };
}

function relationCard(title, items) {
  return `<article class="relation-card"><h3>${esc(title)}</h3>${items.length ? items.map((p) => `<div class="relation-name">${esc(p.cung || '—')}</div><div class="relation-meta">${esc(branchOf(p))} · Cung ${esc(p.cung_so || '—')} · ${(p.chinh_tinh || []).map((x) => starName(x)).join(', ') || '—'}</div>`).join('') : '<div class="relation-meta">Không xác định</div>'}</article>`;
}

function showRelations(p) {
  const r = relationData(p);
  if (!r) return;
  $('relationSubtitle').textContent = `${p.cung || 'Cung'} · ${r.base.branch}`;
  $('relationPanel').innerHTML = relationCard('Tam Hợp', r.tamhop)
    + relationCard('Xung Chiếu', r.xung)
    + relationCard('Nhị Hợp', r.nhihop)
    + relationCard('Giáp Cung', r.giap);
}

function palaceHtml(p, branch) {
  const pos = branches[branch];
  if (!pos) return '';
  if (!p) return `<div class="palace" style="grid-column:${pos[1]};grid-row:${pos[0]};opacity:.45"><div class="phead"><span class="pname">Địa Bàn</span><span class="branch">${branch}</span></div></div>`;
  const menh = norm(p.cung).includes('mệnh');
  const main = asList(p.chinh_tinh);
  const support = supportStars(p);
  const trang = trangSinhName(p);
  return `<button class="palace ${menh ? 'menh' : ''}" style="grid-column:${pos[1]};grid-row:${pos[0]}" data-cung="${esc(p.cung || '')}"><div class="phead"><span class="pname">${esc(p.cung || '—')}${p.than_cu ? '<small>THÂN CƯ</small>' : ''}</span><span class="branch">${branch}</span></div><div class="meta">${esc([p.can_chi, p.ngu_hanh, trang].filter(Boolean).join(' · '))}</div><div class="chips">${stars(main, true)}${stars(support, false)}</div><div class="meta">${p.tuan ? 'Tuần ' : ''}${p.triet ? 'Triệt ' : ''}· Cung ${esc(p.cung_so || '—')}</div></button>`;
}

function renderDetail(p) {
  if (!p) {
    $('detail').classList.add('hidden');
    return;
  }
  $('detail').classList.remove('hidden');
  $('detail').innerHTML = `<div class="card-head"><h2>${esc(p.cung || 'Cung')}</h2><span>${esc(p.can_chi || '')} · ${esc(p.dia_chi || '')}</span></div>
    <div class="summary-row"><span>Chính tinh</span><b>${esc(asList(p.chinh_tinh).map(starName).join(', ') || '—')}</b></div>
    <div class="summary-row"><span>Phụ tinh</span><b>${esc(supportStars(p).map(starName).join(', ') || '—')}</b></div>
    <div class="summary-row"><span>Ngũ hành</span><b>${esc(p.ngu_hanh || '—')}</b></div>
    <div class="summary-row"><span>Trạng thái</span><b>${esc(trangSinhName(p) || '—')}</b></div>
    <button class="ghost small" id="relationDetailBtn">Xem toàn bộ quan hệ cung</button>`;
  $('relationDetailBtn').onclick = () => {
    showRelations(p);
    switchView('relations');
  };
}

function ruleId(x) {
  return x?.rule_id || x?.ruleId || x?.id || x?.rule || '—';
}

function evidenceRows(list) {
  if (!Array.isArray(list) || !list.length) return '<div class="evidence-row">Không có evidence chi tiết.</div>';
  return list.map((ev) => {
    const rel = ev?.relation || ev?.relationship || '';
    const pal = ev?.palace?.cung || ev?.palace?.dia_chi || ev?.cung || ev?.dia_chi || '';
    const s = Array.isArray(ev?.stars) ? ev.stars.join(', ') : (ev?.star || '');
    return `<div class="evidence-row">${esc([rel, pal, s].filter(Boolean).join(' · ') || JSON.stringify(ev))}</div>`;
  }).join('');
}

function renderStarCatalog() {
  const host = $('starCatalog');
  if (!host) return;
  const arr = Object.values(chart?.['12_cung'] || {});
  if (!arr.length) {
    host.innerHTML = '<div class="empty">Lập lá số để xem danh bạ sao.</div>';
    return;
  }
  const map = new Map();
  arr.forEach((palace) => {
    const palaceName = palace?.cung || `Cung ${palace?.cung_so || '—'}`;
    const branch = branchOf(palace) || palace?.dia_chi || '—';
    allStarsInPalace(palace).forEach((star) => {
      const name = starName(star);
      const key = norm(name);
      if (!key) return;
      if (!map.has(key)) {
        map.set(key, {
          name,
          occurrences: 0,
          palaces: [],
          main: false,
          support: false,
          trangSinh: false,
        });
      }
      const item = map.get(key);
      item.occurrences += 1;
      if (!item.palaces.some((x) => x.name === palaceName)) item.palaces.push({ name: palaceName, branch });
      const directMain = asList(palace?.chinh_tinh).some((x) => norm(starName(x)) === key);
      if (directMain || MAIN_STAR_IDS.has(starId(star))) item.main = true;
      if (isTrangSinh(star) || norm(trangSinhName(palace)) === key) item.trangSinh = true;
      if (!directMain && !item.trangSinh) item.support = true;
    });
  });

  const items = [...map.values()].sort((a, b) => b.occurrences - a.occurrences || a.name.localeCompare(b.name, 'vi'));
  host.innerHTML = items.map((item) => {
    const kinds = [item.main ? 'Chính tinh' : '', item.support ? 'Phụ tinh' : '', item.trangSinh ? 'Tràng Sinh' : ''].filter(Boolean);
    return `<article class="star-card">
      <div class="star-card-head">
        <div>${starChip({ ten: item.name }, item.main)}</div>
        <strong>${item.occurrences}</strong>
      </div>
      <div class="star-meta">${esc(kinds.join(' · ') || 'Sao')}${item.palaces.length ? ` · ${item.palaces.length} cung` : ''}</div>
      <div class="star-palaces">${item.palaces.map((p) => `<span class="source-chip">${esc(p.name)} · ${esc(p.branch)}</span>`).join('')}</div>
    </article>`;
  }).join('');
}

function composeAiSourceChips(meta = {}) {
  const chips = [];
  if (meta.provider) chips.push(`<span class="source-chip">AI Provider · ${esc(meta.provider)}</span>`);
  if (meta.mode) chips.push(`<span class="source-chip">AI Mode · ${esc(meta.mode)}</span>`);
  if (meta.year) chips.push(`<span class="source-chip">Năm luận giải · ${esc(meta.year)}</span>`);
  const matched = Array.isArray(chart?.cach_cuc_analysis?.matched) ? chart.cach_cuc_analysis.matched : [];
  const mods = Array.isArray(chart?.cach_cuc_analysis?.modifiers) ? chart.cach_cuc_analysis.modifiers : [];
  matched.concat(mods).forEach((x) => {
    chips.push(`<span class="source-chip">${esc(x.name || 'Cách Cục')} · <span class="rule-id">${esc(ruleId(x))}</span></span>`);
  });
  return chips.join('');
}

function render(c) {
  chart = c;
  const tb = c?.thien_ban || {};
  const arr = Object.values(c?.['12_cung'] || {});
  const menh = palaceByName('Mệnh');
  const matched = Array.isArray(c?.cach_cuc_analysis?.matched) ? c.cach_cuc_analysis.matched : [];
  const mods = Array.isArray(c?.cach_cuc_analysis?.modifiers) ? c.cach_cuc_analysis.modifiers : [];
  const starCount = totalStars(arr);
  $('sMenh').textContent = branchOf(menh) || '—';
  $('sBanMenh').textContent = tb.ban_menh || '—';
  $('sCuc').textContent = tb.ten_cuc || '—';
  $('sCach').textContent = String(starCount);
  $('cachBadge').textContent = String(matched.length + mods.length);
  $('cachCount').textContent = String(matched.length + mods.length);
  $('ruleCount').textContent = String(matched.length);

  const by = new Map();
  arr.forEach((p) => {
    const b = branchOf(p);
    if (b && !by.has(b)) by.set(b, p);
  });
  $('board').innerHTML = order.map((b) => palaceHtml(by.get(b), b)).join('');
  document.querySelectorAll('.palace[data-cung]').forEach((el) => {
    el.onclick = () => {
      const p = palaceByName(el.dataset.cung);
      renderDetail(p);
      showRelations(p);
    };
  });

  const viewingYear = c?.viewing?.year || currentViewYear();
  $('summary').innerHTML = `
    <div class="summary-row"><span>Họ tên</span><b>${esc(tb.ten || '—')}</b></div>
    <div class="summary-row"><span>Can-Chi năm</span><b>${esc([tb.can_nam, tb.chi_nam].filter(Boolean).join(' ') || '—')}</b></div>
    <div class="summary-row"><span>Bản Mệnh</span><b>${esc(tb.ban_menh || '—')}</b></div>
    <div class="summary-row"><span>Mệnh Cục</span><b>${esc(tb.ten_cuc || '—')}</b></div>
    <div class="summary-row"><span>Số lượng sao hiện diện</span><b>${esc(starCount)}</b></div>
    <div class="summary-row"><span>Năm xem</span><b>${esc(viewingYear)}</b></div>
    <div class="summary-row"><span>Mệnh Chủ</span><b>${esc(tb.menh_chu || '—')}</b></div>
    <div class="summary-row"><span>Thân Chủ</span><b>${esc(tb.than_chu || '—')}</b></div>`;

  $('jsonBox').textContent = JSON.stringify(c, null, 2);
  $('aiInfo').innerHTML = `
    <div class="summary-row"><span>12 cung</span><b>${arr.length}</b></div>
    <div class="summary-row"><span>Địa Bàn</span><b>${by.size}/12</b></div>
    <div class="summary-row"><span>Cách Cục</span><b>${matched.length + mods.length}</b></div>
    <div class="summary-row"><span>Rule có evidence</span><b>${matched.filter((x) => x?.matched_branches?.length || x?.evidence?.length).length}</b></div>
    <div class="summary-row"><span>Cung Mệnh</span><b>${esc(branchOf(menh) || '—')}</b></div>
    <div class="summary-row"><span>Số sao hiện diện</span><b>${esc(starCount)}</b></div>
    <div class="summary-row"><span>Năm xem</span><b>${esc(viewingYear)}</b></div>`;
  $('aiSources').innerHTML = composeAiSourceChips({ year: viewingYear });
  renderCach();
  renderStarCatalog();
  switchView('chart');
  upsertProfile();
}

function renderCach() {
  const a = chart?.cach_cuc_analysis || {};
  const matched = Array.isArray(a.matched) ? a.matched : [];
  const mods = Array.isArray(a.modifiers) ? a.modifiers : [];
  const items = [];
  const seen = new Set();
  const add = (x, desc, cat, evi) => {
    const name = x?.name || 'Cách Cục';
    const k = norm(name);
    if (!k || seen.has(k)) return;
    seen.add(k);
    items.push(`<article class="cach-item"><h3>${esc(name)}</h3><div class="cach-meta"><span class="tag">${esc(cat || 'Engine')}</span><span class="tag">Rule ID: <span class="rule-id">${esc(ruleId(x))}</span></span></div><div>${esc(desc || '')}</div><div class="evidence"><b>Evidence</b><div class="evidence-grid">${evidenceRows(evi)}</div></div></article>`);
  };
  matched.forEach((x) => x && add(x, x.description || x.reason || '', x.category || 'Engine', x.matched_branches || x.evidence || []));
  mods.forEach((x) => x && add(x, x.interpretation || x.ai_instruction || '', 'Engine modifier', x.breaking_evidence || x.evidence || []));
  $('cachList').innerHTML = items.length ? items.join('') : '<div class="empty">Chưa có Cách Cục được xác định.</div>';
}

async function call(url, opt = {}) {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opt });
  const d = await r.json();
  if (!r.ok) throw Error(d.detail || 'Request failed');
  return d;
}

function payload() {
  return {
    ngay: +$('day').value,
    thang: +$('month').value,
    nam: +$('year').value,
    gio_sinh: $('hour').value,
    gioi_tinh: $('gender').value,
    ten: $('name').value,
    duong_lich: $('calendar').value === 'true',
    time_zone: +$('tz').value,
    nam_xem: currentViewYear(),
  };
}

async function lapSo() {
  const b = $('calcBtn');
  b.disabled = true;
  $('status').textContent = 'Đang lập lá số...';
  try {
    await branchCatalogReady;
    const d = await call('/api/lap-so', { method: 'POST', body: JSON.stringify(payload()) });
    render(d);
    $('status').textContent = 'Đã lập lá số';
  } catch (e) {
    $('status').textContent = e.message;
  } finally {
    b.disabled = false;
  }
}

const titles = {
  chart: 'Thiên Bàn & 12 Địa Bàn',
  cach: 'Cách Cục',
  stars: 'Danh bạ sao',
  relations: 'Quan hệ cung',
  ai: 'AI luận giải',
  audit: 'AI Evidence / Audit',
  data: 'Dữ liệu engine',
};

function switchView(name) {
  document.querySelectorAll('.nav').forEach((x) => x.classList.toggle('active', x.dataset.view === name));
  document.querySelectorAll('.view').forEach((x) => x.classList.toggle('active', x.id === `view-${name}`));
  $('pageTitle').textContent = titles[name] || name;
}

function extractSectionHeadings(text) {
  return [...new Set((text.match(/^#{1,3}\s+.+$/gm) || []).map((x) => x.replace(/^#+\s+/, '').trim()).slice(0, 16))];
}

function showToc() {
  const heads = extractSectionHeadings(lastAnswer);
  if (!heads.length) {
    $('tocBtn').textContent = 'Không có mục lục';
    setTimeout(() => { $('tocBtn').textContent = 'Mục lục'; }, 1200);
    return;
  }
  document.getElementById('currentToc')?.remove();
  const wrap = document.createElement('div');
  wrap.className = 'toc show';
  wrap.id = 'currentToc';
  wrap.innerHTML = heads.map((h, i) => `<button data-toc-index="${i}">${esc(h)}</button>`).join('');
  const chat = $('chat');
  chat.prepend(wrap);
  wrap.querySelectorAll('button').forEach((btn) => {
    btn.onclick = () => {
      const n = Number(btn.dataset.tocIndex);
      const target = document.querySelector(`[data-section-index="${n}"]`);
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };
  });
}

function buildStreamHtml(text) {
  const lines = text.split(/\n/);
  let html = '';
  let section = 0;
  for (const line of lines) {
    const m = line.match(/^#{1,3}\s+(.+)$/);
    if (m) {
      html += `<h3 data-section-index="${section}">${esc(m[1])}</h3>`;
      section += 1;
    } else if (line.trim()) {
      html += `<p>${esc(line)}</p>`;
    }
  }
  return html || `<p>${esc(text)}</p>`;
}

async function streamAnswer(text) {
  const id = `answer-${Date.now()}`;
  $('chat').insertAdjacentHTML('beforeend', `<div class="msg-bubble assistant" id="${id}"><small>AI Tử Vi</small><div class="answer-text"></div><span class="stream-cursor"></span></div>`);
  const box = $(id);
  const out = box.querySelector('.answer-text');
  const chars = text.length;
  for (let i = 0; i < chars; i += 18) {
    out.textContent = text.slice(0, i + 18);
    $('chat').scrollTop = $('chat').scrollHeight;
    // eslint-disable-next-line no-await-in-loop
    await new Promise((r) => setTimeout(r, 3));
  }
  out.innerHTML = buildStreamHtml(text);
  box.querySelector('.stream-cursor')?.remove();
  $('chat').scrollTop = $('chat').scrollHeight;
  return id;
}

function auditAnswer(text) {
  const a = chart?.cach_cuc_analysis || {};
  const confirmed = [...(a.matched || []), ...(a.modifiers || [])].filter((x) => x && x.name);
  const names = confirmed.map((x) => x.name);
  const hits = names.filter((n) => text.toLowerCase().includes(String(n).toLowerCase()));
  const cachTerms = [...new Set((text.match(/[^\n]{0,60}Cách Cục[^\n]{0,30}/gi) || []).map((x) => x.trim()))];
  const unverified = cachTerms.filter((t) => !names.some((n) => t.toLowerCase().includes(String(n).toLowerCase())));
  const withRule = confirmed.map((x) => ({
    name: x.name,
    id: ruleId(x),
    evidence: Array.isArray(x.matched_branches) ? x.matched_branches.length : (Array.isArray(x.evidence) ? x.evidence.length : (Array.isArray(x.breaking_evidence) ? x.breaking_evidence.length : 0)),
  }));
  $('auditStatus').textContent = unverified.length ? 'AUDIT WARNING' : 'AUDIT PASS';
  $('auditStatus').className = unverified.length ? 'warn' : 'ok';
  $('auditResult').innerHTML = `<div class="${unverified.length ? 'audit-warn' : 'audit-ok'}"><b>${unverified.length ? '⚠ Cần kiểm tra tên Cách Cục' : '✓ Audit không phát hiện tên Cách Cục tự sinh rõ ràng'}</b><div style="margin-top:6px">Engine xác nhận: ${names.length} · AI dùng tên có trong engine: ${hits.length}</div></div><div class="cach-list" style="margin-top:10px">${withRule.map((x) => `<div class="cach-item"><b>${esc(x.name)}</b><div class="cach-meta"><span class="tag">Rule ID: <span class="rule-id">${esc(x.id)}</span></span><span class="tag">Evidence: ${x.evidence}</span></div></div>`).join('') || '<div class="empty">Chưa có Rule match.</div>'}${unverified.map((x) => `<div class="audit-warn"><b>Không truy được Engine:</b> ${esc(x)}</div>`).join('')}</div>`;
  return { hits, unverified };
}

async function askAI() {
  if (!chart) return;
  const q = $('question').value.trim();
  if (!q) return;
  $('askBtn').disabled = true;
  $('chat').insertAdjacentHTML('beforeend', `<div class="msg-bubble user"><small>Bạn</small>${esc(q)}</div><div id="typing" class="msg-bubble assistant"><small>AI Tử Vi</small>Đang luận giải...</div>`);
  $('question').value = '';
  $('chat').scrollTop = $('chat').scrollHeight;
  try {
    const d = await call('/api/luan-giai', { method: 'POST', body: JSON.stringify({ ...payload(), question: q, year: currentViewYear() }) });
    $('typing')?.remove();
    if (d?.van && chart) {
      chart.van = d.van;
      chart.viewing = { ...(chart.viewing || {}), year: d.year || currentViewYear() };
      $('jsonBox').textContent = JSON.stringify(chart, null, 2);
      $('aiInfo').innerHTML += `<div class="summary-row"><span>AI Provider</span><b>${esc(d.ai_provider || '—')}</b></div><div class="summary-row"><span>AI Mode</span><b>${esc(d.ai_mode || '—')}</b></div>`;
      $('aiSources').innerHTML = composeAiSourceChips({ provider: d.ai_provider, mode: d.ai_mode, year: d.year });
    }
    lastAnswer = d.answer || 'Chưa có phản hồi';
    await streamAnswer(lastAnswer);
    auditAnswer(lastAnswer);
    $('runAuditBtn').click();
    $('aiInfo').innerHTML += `<div class="summary-row"><span>Audit</span><b>${$('auditStatus').textContent}</b></div>`;
  } catch (e) {
    $('typing')?.remove();
    $('chat').insertAdjacentHTML('beforeend', `<div class="msg-bubble assistant"><small>Lỗi</small>${esc(e.message)}</div>`);
  } finally {
    $('askBtn').disabled = false;
  }
}

function reset() {
  chart = null;
  lastAnswer = '';
  $('status').textContent = '';
  $('sMenh').textContent = '—';
  $('sBanMenh').textContent = '—';
  $('sCuc').textContent = '—';
  $('sCach').textContent = '0';
  $('cachBadge').textContent = '0';
  $('cachCount').textContent = '0';
  $('ruleCount').textContent = '—';
  $('board').innerHTML = '';
  $('summary').textContent = 'Chưa có dữ liệu.';
  $('cachList').innerHTML = '<div class="empty">Chưa có Cách Cục được xác định.</div>';
  $('starCatalog').innerHTML = '<div class="empty">Lập lá số để xem danh bạ sao.</div>';
  $('jsonBox').textContent = 'Chưa có dữ liệu.';
  $('aiInfo').textContent = 'Chưa có lá số.';
  $('aiSources').innerHTML = '';
  $('chat').innerHTML = '<div class="assistant msg-bubble"><small>AI Tử Vi</small>Hãy lập lá số rồi đặt câu hỏi.</div>';
  $('detail').classList.add('hidden');
  $('relationPanel').innerHTML = '<div class="empty">Chọn một cung để xem quan hệ.</div>';
  $('auditResult').innerHTML = '<div class="empty">Chưa có bài luận để kiểm tra.</div>';
  $('van10Panel').innerHTML = '';
  switchView('chart');
}

$('calcBtn').onclick = lapSo;
$('resetBtn').onclick = reset;
$('askBtn').onclick = askAI;
$('runAuditBtn').onclick = () => { if (lastAnswer) auditAnswer(lastAnswer); };
$('tocBtn').onclick = showToc;
$('printBtn')?.addEventListener('click', () => window.print());
$('aiSettingsBtn')?.addEventListener('click', () => { window.location.href = '/ai-mode'; });
$('newProfileBtn').onclick = () => {
  ['name'].forEach((k) => { $(k).value = ''; });
  $('day').value = 1;
  $('month').value = 1;
  $('year').value = 1996;
  $('hour').value = 'Tý';
  $('gender').value = 'Nam';
  $('calendar').value = 'true';
  $('tz').value = 7;
  if ($('viewYear')) $('viewYear').value = String(new Date().getFullYear());
  $('profileSelect').value = '';
  $('profileId').textContent = 'ID: —';
};
$('profileSelect').onchange = (e) => loadProfile(e.target.value);
document.querySelectorAll('.nav').forEach((b) => b.onclick = () => switchView(b.dataset.view));
$('question').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    askAI();
  }
});
if ($('viewYear') && !$('viewYear').value) $('viewYear').value = String(new Date().getFullYear());
refreshProfiles();
renderStarCatalog();
