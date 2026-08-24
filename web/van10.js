(() => {
  const $ = (id) => document.getElementById(id);
  const yearInput = $('viewYear');
  const jsonBox = $('jsonBox');
  const currentYear = new Date().getFullYear();

  if (yearInput) {
    yearInput.value = String(Number(yearInput.value) || currentYear);
    yearInput.addEventListener('change', () => {
      const y = Math.min(2200, Math.max(1800, Number(yearInput.value) || currentYear));
      yearInput.value = String(Math.trunc(y));
      renderFromJson();
    });
  }

  // Keep the existing core app.js untouched while making the viewing year authoritative.
  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (input, init = {}) => {
    const url = typeof input === 'string' ? input : input?.url || '';
    const isTarget = url.includes('/api/lap-so') || url.includes('/api/luan-giai');
    if (isTarget && init.body && typeof init.body === 'string') {
      try {
        const body = JSON.parse(init.body);
        const y = Number(yearInput?.value);
        if (Number.isInteger(y) && y >= 1800 && y <= 2200) {
          body.nam_xem = y;
          if (url.includes('/api/luan-giai')) body.year = y;
          init = { ...init, body: JSON.stringify(body) };
        }
      } catch (_) {}
    }
    return nativeFetch(input, init);
  };

  const asList = (value) => {
    if (Array.isArray(value)) return value;
    if (value && typeof value === 'object') return Object.values(value);
    return [];
  };

  const firstList = (van, ...keys) => {
    for (const key of keys) {
      const list = asList(van?.[key]);
      if (list.length) return list;
    }
    return [];
  };

  const text = (v) => v == null || v === '' ? '—' : String(v);
  const branch = (x) => text(x?.chi_ten ?? x?.dia_chi ?? x?.chi ?? x?.branch);
  const palace = (x) => text(x?.cung ?? (x?.cung_so != null ? `Cung ${x.cung_so}` : '—'));
  const stars = (x) => {
    const value = x?.chinh_tinh ?? x?.stars ?? x?.sao ?? [];
    return Array.isArray(value) ? value.map(s => s?.ten ?? s?.name ?? s).join(', ') || '—' : text(value);
  };

  const escapeHtml = (value) => String(value ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

  const compact = (item) => {
    const name = palace(item);
    const b = branch(item);
    const cc = text(item?.can_chi);
    const st = stars(item);
    return `<b>${escapeHtml(name)}</b><span class="muted">${escapeHtml([b, cc].filter(x => x !== '—').join(' · ') || '—')}</span><span class="muted">${escapeHtml(st)}</span>`;
  };

  function renderVan10(chart) {
    const host = $('van10Panel');
    if (!host) return;
    const van = chart?.van || {};
    const dv = asList(van.dai_van_10_nam);
    const lndv = firstList(van, 'luu_nien_dai_van_10_nam', 'luu_dai_van_10_nam');
    const tv = firstList(van, 'tieu_van_10_nam', 'luu_nien_tieu_van_10_nam');
    const lnn = firstList(van, 'luu_nien_nam_10_nam', 'luu_nien_tieu_van_10_nam');
    const rows = [];
    for (let i = 0; i < 10; i += 1) {
      const a = dv[i] || {};
      const b = lndv[i] || {};
      const c = tv[i] || {};
      const d = lnn[i] || {};
      const year = a.nam ?? b.nam ?? c.nam ?? d.nam ?? '—';
      const age = a.tuoi ?? b.tuoi ?? c.tuoi ?? d.tuoi ?? '—';
      rows.push(`<tr class="${Number(year) === Number(yearInput?.value) ? 'is-viewing' : ''}">
        <td><button class="year-pick" type="button" data-year="${escapeHtml(year)}">${escapeHtml(year)}</button></td>
        <td>${escapeHtml(age)}</td>
        <td>${compact(a)}</td>
        <td>${compact(b)}</td>
        <td>${compact(c)}</td>
        <td>${compact(d)}</td>
      </tr>`);
    }
    host.innerHTML = `<section class="card van10-card">
      <div class="card-head"><div><h2>Vận hạn 10 năm</h2><span>4 lớp dữ liệu authoritative từ engine</span></div><strong>${rows.length}</strong></div>
      <div class="van10-note">Năm chọn ở trên được gửi trực tiếp vào <b>nam_xem</b> và <b>year</b>; bảng chỉ hiển thị dữ liệu vận hạn do engine trả về.</div>
      <div class="van10-wrap"><table class="van10"><thead><tr><th>Năm</th><th>Tuổi</th><th>Đại vận</th><th>Lưu niên Đại vận</th><th>Tiểu vận</th><th>Lưu niên năm</th></tr></thead><tbody>${rows.join('')}</tbody></table></div>
    </section>`;
    host.querySelectorAll('.year-pick').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!yearInput) return;
        yearInput.value = btn.dataset.year;
        renderFromJson();
      });
    });
  }

  function renderFromJson() {
    try {
      const host = $('van10Panel');
      if (!jsonBox) return;
      const raw = jsonBox.textContent.trim();
      if (!raw || raw === 'Chưa có dữ liệu.') {
        if (host) host.innerHTML = '';
        return;
      }
      const chart = JSON.parse(raw);
      renderVan10(chart);
    } catch (_) {}
  }

  if (jsonBox) {
    new MutationObserver(renderFromJson).observe(jsonBox, { childList: true, subtree: true, characterData: true });
  }
  setTimeout(renderFromJson, 0);
  window.renderVan10 = renderVan10;
})();
