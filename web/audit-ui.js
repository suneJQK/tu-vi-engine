(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const asList = (v) => Array.isArray(v) ? v : (v && typeof v === 'object' ? Object.values(v) : []);
  const starName = (s) => s?.ten || s?.name || s?.saoTen || s?.sao || String(s ?? '');
  const starNames = (list) => asList(list).map(starName).filter(Boolean);

  function readChart() {
    try {
      const raw = $('jsonBox')?.textContent || '';
      return raw && raw !== 'Chưa có dữ liệu.' ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function evidenceCount(item) {
    const candidates = [item?.evidence, item?.matched_branches, item?.breaking_evidence];
    return candidates.reduce((n, v) => n + (Array.isArray(v) ? v.length : 0), 0);
  }

  function auditChart() {
    const chart = readChart();
    const result = $('auditResult');
    const status = $('auditStatus');
    if (!result) return;
    if (!chart) {
      result.innerHTML = '<div class="audit-warn"><b>Không có dữ liệu chart.</b><div style="margin-top:6px">Hãy lập lá số trước khi chạy Audit.</div></div>';
      if (status) status.textContent = 'AUDIT WARNING';
      return;
    }

    const palaces = asList(chart['12_cung']);
    const cach = chart?.cach_cuc_analysis || {};
    const matched = asList(cach.matched);
    const modifiers = asList(cach.modifiers);
    const lines = [];

    lines.push(`<div class="audit-ok"><b>✓ Chart loaded</b><div style="margin-top:6px">12 cung: ${palaces.length}/12 · Cách Cục: ${matched.length} · Modifiers: ${modifiers.length}</div></div>`);

    const missing = [];
    palaces.forEach((p, i) => {
      const name = p?.cung || `Cung ${i + 1}`;
      const main = asList(p?.chinh_tinh);
      const support = asList(p?.phu_tinh);
      const raw = asList(p?.sao);
      const trang = p?.trang_sinh || p?.vong_trang_sinh || (asList(p?.vong_trang_sinh_data)[0] ? starName(asList(p?.vong_trang_sinh_data)[0]) : '');
      if (!support.length && raw.length) missing.push(name);
      lines.push(`<div class="cach-item"><b>${esc(name)}</b><div class="cach-meta"><span class="tag">Chính tinh: ${main.length}</span><span class="tag">Phụ tinh: ${support.length}</span><span class="tag">Sao gốc: ${raw.length}</span><span class="tag">Tràng Sinh: ${esc(trang || '—')}</span></div></div>`);
    });

    if (matched.length || modifiers.length) {
      lines.push('<div class="card-head" style="margin-top:14px"><h3>Evidence Cách Cục</h3></div>');
      [...matched, ...modifiers].forEach((item) => {
        const name = item?.name || 'Cách Cục';
        lines.push(`<div class="evidence-row"><b>${esc(name)}</b> · Rule: ${esc(item?.id || item?.rule_id || item?.ruleId || '—')} · Evidence: ${evidenceCount(item)}</div>`);
      });
    }

    if (missing.length) {
      lines.unshift(`<div class="audit-warn"><b>⚠ Có cung chứa sao gốc nhưng phu_tinh rỗng:</b> ${esc(missing.join(', '))}</div>`);
    } else {
      lines.unshift('<div class="audit-ok"><b>✓ Mapping phụ tinh hợp lệ</b><div style="margin-top:6px">Không phát hiện cung nào có sao gốc nhưng thiếu trường phu_tinh.</div></div>');
    }

    result.innerHTML = lines.join('');
    if (status) {
      status.textContent = missing.length ? 'AUDIT WARNING' : 'AUDIT PASS';
      status.className = missing.length ? 'warn' : 'ok';
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    const btn = $('runAuditBtn');
    if (btn) btn.addEventListener('click', auditChart);
  });
})();
