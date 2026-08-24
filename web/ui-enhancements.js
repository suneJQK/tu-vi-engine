(() => {
  const $ = (id) => document.getElementById(id);
  const PROFILE_KEY = 'tvai_profiles_v2';
  const ESCAPE = (value) => String(value ?? '').replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m] || m));
  const ORDER = ['Hợi', 'Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất'];
  const ELEMENTS = [
    { key: 'moc', label: 'Mộc', tone: 'wood' },
    { key: 'hoa', label: 'Hỏa', tone: 'fire' },
    { key: 'tho', label: 'Thổ', tone: 'earth' },
    { key: 'kim', label: 'Kim', tone: 'metal' },
    { key: 'thuy', label: 'Thủy', tone: 'water' },
  ];
  const RELATIONS = [
    { key: 'base', label: 'Cung chọn', cls: 'rel-base' },
    { key: 'tamhop', label: 'Tam Hợp', cls: 'rel-tamhop' },
    { key: 'xung', label: 'Xung Chiếu', cls: 'rel-xung' },
    { key: 'nhihop', label: 'Nhị Hợp', cls: 'rel-nhihop' },
    { key: 'giap', label: 'Giáp Cung', cls: 'rel-giap' },
  ];

  const normalize = (value) => String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .trim()
    .toLowerCase();

  function asList(value) {
    if (Array.isArray(value)) return value;
    if (value && typeof value === 'object') return Object.values(value);
    return [];
  }

  function allPalaces() {
    return asList(window.chart?.['12_cung']);
  }

  function matchElementName(raw) {
    const s = normalize(raw);
    if (s.includes('moc')) return 'moc';
    if (s.includes('hoa')) return 'hoa';
    if (s.includes('tho')) return 'tho';
    if (s.includes('kim')) return 'kim';
    if (s.includes('thuy')) return 'thuy';
    return '';
  }

  function starName(star) {
    return star?.ten || star?.name || star?.saoTen || star?.sao || String(star ?? '');
  }

  function mainStarsOf(palace) {
    return asList(palace?.chinh_tinh).map(starName).filter(Boolean);
  }

  function supportStarsOf(palace) {
    const direct = asList(palace?.phu_tinh || palace?.phuTinh);
    if (direct.length) return direct.map(starName).filter(Boolean);
    const raw = asList(palace?.sao || palace?.stars || palace?.all_stars);
    return raw.map(starName).filter(Boolean).slice(0, 10);
  }

  function renderLegend() {
    const host = $('nguHanhLegend');
    if (!host) return;
    const counts = { moc: 0, hoa: 0, tho: 0, kim: 0, thuy: 0 };
    allPalaces().forEach((palace) => {
      const key = matchElementName(palace?.ngu_hanh);
      if (key) counts[key] += 1;
    });
    host.innerHTML = ELEMENTS.map((item) => `<span class="legend-chip ${item.tone}"><b>${item.label}</b><span>${counts[item.key] || 0} cung</span></span>`).join('');
    const relationHost = $('relationLegend');
    if (relationHost) {
      relationHost.innerHTML = RELATIONS.map((item) => `<span class="legend-chip ${item.cls}">${item.label}</span>`).join('');
    }
  }

  function boardButtonByBranch(branch) {
    const buttons = Array.from(document.querySelectorAll('#board .palace[data-cung]'));
    return buttons.find((btn) => {
      const palace = window.palaceByName?.(btn.dataset.cung);
      return palace && window.branchOf?.(palace) === branch;
    }) || null;
  }

  function applyRelationHighlight(palace) {
    const buttons = Array.from(document.querySelectorAll('#board .palace'));
    buttons.forEach((btn) => {
      btn.classList.remove('is-selected', 'relation-base', 'relation-tamhop', 'relation-xung', 'relation-nhihop', 'relation-giap');
    });
    if (!palace || !window.relationData) return;
    const rel = window.relationData(palace);
    const baseBranch = rel?.base?.branch;
    if (baseBranch) boardButtonByBranch(baseBranch)?.classList.add('is-selected', 'relation-base');
    rel?.tamhop?.forEach((item) => boardButtonByBranch(window.branchOf?.(item))?.classList.add('relation-tamhop'));
    rel?.xung?.forEach((item) => boardButtonByBranch(window.branchOf?.(item))?.classList.add('relation-xung'));
    rel?.nhihop?.forEach((item) => boardButtonByBranch(window.branchOf?.(item))?.classList.add('relation-nhihop'));
    rel?.giap?.forEach((item) => boardButtonByBranch(window.branchOf?.(item))?.classList.add('relation-giap'));
  }

  function renderSelectionSummary(palace) {
    const host = $('selectionSummary');
    if (!host) return;
    if (!palace) {
      host.classList.add('empty-state');
      host.innerHTML = 'Chưa chọn cung.';
      return;
    }
    host.classList.remove('empty-state');
    const rel = window.relationData?.(palace);
    const elem = palace?.ngu_hanh || '—';
    const main = mainStarsOf(palace).slice(0, 3);
    const support = supportStarsOf(palace).slice(0, 4);
    const badge = (label, items, cls) => `<span class="legend-chip ${cls}">${label}: <b>${items.length}</b></span>`;
    host.innerHTML = `
      <div class="title-row">
        <div>
          <b>${ESCAPE(palace?.cung || '—')}</b>
          <div class="muted">${ESCAPE([window.branchOf?.(palace), palace?.can_chi, elem].filter(Boolean).join(' · '))}</div>
        </div>
        <div class="relation-badges">
          ${badge('Tam Hợp', rel?.tamhop || [], 'rel-tamhop')}
          ${badge('Xung', rel?.xung || [], 'rel-xung')}
          ${badge('Nhị Hợp', rel?.nhihop || [], 'rel-nhihop')}
          ${badge('Giáp', rel?.giap || [], 'rel-giap')}
        </div>
      </div>
      <div class="star-preview">${main.map((name) => `<span class="chip main">${ESCAPE(name)}</span>`).join('') || '<span class="chip">Không có chính tinh</span>'}</div>
      <div class="star-preview">${support.map((name) => `<span class="chip">${ESCAPE(name)}</span>`).join('') || '<span class="chip">Không có phụ tinh</span>'}</div>
    `;
  }

  function enrichRelationPanel(palace) {
    const host = $('relationPanel');
    if (!host || !palace || !window.relationData) return;
    const rel = window.relationData(palace);
    const groups = [
      ['Tam Hợp', rel?.tamhop || [], 'rel-tamhop'],
      ['Xung Chiếu', rel?.xung || [], 'rel-xung'],
      ['Nhị Hợp', rel?.nhihop || [], 'rel-nhihop'],
      ['Giáp Cung', rel?.giap || [], 'rel-giap'],
    ];
    host.innerHTML = groups.map(([label, items, cls]) => `
      <article class="relation-card">
        <h3>${label}</h3>
        ${items.length ? items.map((item) => `
          <div class="relation-name">${ESCAPE(item?.cung || '—')}</div>
          <div class="relation-meta">${ESCAPE([window.branchOf?.(item), item?.cung_so ? `Cung ${item.cung_so}` : '', mainStarsOf(item).join(', ')].filter(Boolean).join(' · '))}</div>
          <div class="relation-actions"><button type="button" class="ghost small relation-jump ${cls}" data-cung="${ESCAPE(item?.cung || '')}">Định vị cung</button></div>
        `).join('') : '<div class="relation-meta">Không xác định</div>'}
      </article>
    `).join('');

    host.querySelectorAll('.relation-jump').forEach((btn) => {
      btn.addEventListener('click', () => {
        const target = window.palaceByName?.(btn.dataset.cung);
        if (!target) return;
        applyRelationHighlight(target);
        renderSelectionSummary(target);
        window.renderDetail?.(target);
        const boardBtn = document.querySelector(`#board .palace[data-cung="${CSS.escape(btn.dataset.cung)}"]`);
        boardBtn?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        boardBtn?.click();
      });
    });
  }

  function enrichBoardData() {
    document.querySelectorAll('#board .palace[data-cung]').forEach((btn) => {
      const palace = window.palaceByName?.(btn.dataset.cung);
      const key = matchElementName(palace?.ngu_hanh);
      if (key) btn.dataset.nguhanh = key;
      btn.title = [palace?.cung, palace?.ngu_hanh, window.branchOf?.(palace)].filter(Boolean).join(' · ');
    });
  }

  function filterStarCatalog(term) {
    const cards = Array.from(document.querySelectorAll('#starCatalog .star-card'));
    if (!cards.length) return;
    const normalized = normalize(term);
    cards.forEach((card) => {
      const text = normalize(card.textContent);
      card.style.display = !normalized || text.includes(normalized) ? '' : 'none';
    });
  }

  async function copyJson() {
    const raw = $('jsonBox')?.textContent?.trim();
    if (!raw || raw === 'Chưa có dữ liệu.') return;
    try {
      await navigator.clipboard.writeText(raw);
      const btn = $('copyJsonBtn') || $('copyJsonInlineBtn');
      if (btn) {
        const old = btn.textContent;
        btn.textContent = 'Đã sao chép';
        setTimeout(() => { btn.textContent = old; }, 1200);
      }
    } catch (_) {}
  }

  function exportProfiles() {
    try {
      const data = JSON.parse(localStorage.getItem(PROFILE_KEY) || '[]');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'tvai-profiles.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch (_) {}
  }

  function importProfiles(file) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const incoming = JSON.parse(String(reader.result || '[]'));
        const current = JSON.parse(localStorage.getItem(PROFILE_KEY) || '[]');
        const map = new Map();
        current.concat(Array.isArray(incoming) ? incoming : []).forEach((item) => {
          if (item?.id) map.set(item.id, item);
        });
        localStorage.setItem(PROFILE_KEY, JSON.stringify(Array.from(map.values())));
        window.refreshProfiles?.();
        $('status').textContent = `Đã nhập ${map.size} hồ sơ.`;
      } catch (error) {
        $('status').textContent = 'Không đọc được file hồ sơ JSON.';
      }
    };
    reader.readAsText(file);
  }

  function toggleBoardFocus() {
    document.body.classList.toggle('full-focus');
    const btn = $('focusBoardBtn');
    if (btn) btn.textContent = document.body.classList.contains('full-focus') ? 'Thoát tập trung' : 'Tập trung bàn số';
  }

  function hookButtons() {
    $('starSearch')?.addEventListener('input', (e) => filterStarCatalog(e.target.value));
    $('copyJsonBtn')?.addEventListener('click', copyJson);
    $('copyJsonInlineBtn')?.addEventListener('click', copyJson);
    $('exportProfileBtn')?.addEventListener('click', exportProfiles);
    $('importProfileBtn')?.addEventListener('click', () => $('importProfileInput')?.click());
    $('importProfileInput')?.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (file) importProfiles(file);
      e.target.value = '';
    });
    $('focusBoardBtn')?.addEventListener('click', toggleBoardFocus);
  }

  function patchRenderLifecycle() {
    if (typeof window.render === 'function' && !window.render.__enhanced) {
      const nativeRender = window.render;
      window.render = function patchedRender(...args) {
        const result = nativeRender.apply(this, args);
        renderLegend();
        enrichBoardData();
        filterStarCatalog($('starSearch')?.value || '');
        renderSelectionSummary(null);
        return result;
      };
      window.render.__enhanced = true;
    }
    if (typeof window.showRelations === 'function' && !window.showRelations.__enhanced) {
      const nativeShowRelations = window.showRelations;
      window.showRelations = function patchedShowRelations(palace) {
        const result = nativeShowRelations.apply(this, arguments);
        applyRelationHighlight(palace);
        renderSelectionSummary(palace);
        enrichRelationPanel(palace);
        return result;
      };
      window.showRelations.__enhanced = true;
    }
    if (typeof window.renderDetail === 'function' && !window.renderDetail.__enhanced) {
      const nativeRenderDetail = window.renderDetail;
      window.renderDetail = function patchedRenderDetail(palace) {
        const result = nativeRenderDetail.apply(this, arguments);
        applyRelationHighlight(palace);
        renderSelectionSummary(palace);
        return result;
      };
      window.renderDetail.__enhanced = true;
    }
    if (typeof window.reset === 'function' && !window.reset.__enhanced) {
      const nativeReset = window.reset;
      window.reset = function patchedReset() {
        const result = nativeReset.apply(this, arguments);
        renderLegend();
        renderSelectionSummary(null);
        filterStarCatalog('');
        document.body.classList.remove('full-focus');
        const btn = $('focusBoardBtn');
        if (btn) btn.textContent = 'Tập trung bàn số';
        return result;
      };
      window.reset.__enhanced = true;
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    hookButtons();
    patchRenderLifecycle();
    renderLegend();
    renderSelectionSummary(null);
    document.querySelector('#board')?.addEventListener('click', (event) => {
      const button = event.target.closest('.palace[data-cung]');
      if (!button) return;
      const palace = window.palaceByName?.(button.dataset.cung);
      if (palace) {
        setTimeout(() => {
          applyRelationHighlight(palace);
          renderSelectionSummary(palace);
        }, 0);
      }
    });
  });
})();
