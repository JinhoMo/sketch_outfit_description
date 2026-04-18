"""Render Identity Consulting Report as standalone HTML."""
import base64
from io import BytesIO
from typing import List, Optional

from jinja2 import Template
from PIL import Image

TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Sketch. Identity Consulting Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Noto+Sans+KR:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #f5f3ef;
    --border: #c8c2b8;
    --dark: #1a1a1a;
    --mid: #4a4a4a;
    --light: #7a7a7a;
  }

  body {
    background: #e8e4de;
    font-family: 'Noto Sans KR', sans-serif;
    display: flex;
    justify-content: center;
    padding: 32px 16px;
    min-height: 100vh;
  }

  .page {
    background: var(--bg);
    width: 794px;
    padding: 40px 44px 36px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.12);
  }

  /* HEADER */
  .header {
    display: grid;
    grid-template-columns: 1fr 240px;
    gap: 28px;
    margin-bottom: 24px;
    align-items: start;
  }
  .brand {
    font-family: 'Playfair Display', serif;
    font-size: 68px;
    font-weight: 900;
    letter-spacing: -1.5px;
    line-height: 1;
    color: var(--dark);
  }
  .tagline {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 22px;
    font-weight: 700;
    color: var(--dark);
    margin-top: 4px;
    letter-spacing: 0.5px;
  }
  .subtitle {
    font-family: 'EB Garamond', serif;
    font-size: 15px;
    color: var(--mid);
    margin-top: 6px;
    letter-spacing: 1.8px;
  }
  .header-photo-wrap { display: flex; flex-direction: column; }
  .header-photo, .header-photo-ph {
    width: 100%;
    aspect-ratio: 3/4;
    object-fit: cover;
    object-position: top center;
    display: block;
  }
  .header-photo-caption {
    font-family: 'EB Garamond', serif;
    font-size: 11px;
    font-style: italic;
    color: var(--light);
    margin-top: 6px;
    text-align: center;
    letter-spacing: 0.3px;
  }
  .header-photo-ph {
    background: linear-gradient(135deg, #d0ccc6 0%, #b8b2aa 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    color: #888;
    letter-spacing: 1px;
  }

  /* GRIDS */
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  .grid-2.wide-left { grid-template-columns: 1.6fr 1fr; }
  .cell { padding: 16px 20px 20px; }
  .cell.br { border-right: 1px solid var(--border); }
  .row-top { border-top: 1px solid var(--border); }
  .row-bt { border-bottom: 1px solid var(--border); }

  /* SECTION HEADINGS */
  .sec-head {
    font-family: 'Playfair Display', serif;
    font-size: 19px;
    font-weight: 700;
    color: var(--dark);
    padding: 14px 20px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .sec-head.right { text-align: right; }
  .section-heading {
    font-family: 'Playfair Display', serif;
    font-size: 18px;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 12px;
    letter-spacing: 0.3px;
  }
  .col-title {
    font-family: 'Playfair Display', serif;
    font-size: 15px;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 12px;
  }

  .info-row {
    font-size: 12px;
    color: var(--mid);
    line-height: 1.95;
  }
  .info-row span {
    color: var(--dark);
    font-weight: 500;
  }

  /* check + bullets */
  .check {
    font-size: 11.5px;
    font-weight: 500;
    color: var(--dark);
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .check::before { content: '✓'; font-size: 11px; color: var(--dark); }

  .bullets { list-style: none; padding: 0; margin-bottom: 10px; }
  .bullets li {
    font-size: 11px;
    color: var(--mid);
    line-height: 1.8;
    padding-left: 9px;
    position: relative;
  }
  .bullets li::before {
    content: '';
    position: absolute;
    left: 0;
    top: 9px;
    width: 3px;
    height: 3px;
    background: var(--mid);
    border-radius: 50%;
  }

  .rec-list { list-style: none; padding: 0; }
  .rec-list li {
    font-size: 11.5px;
    color: var(--mid);
    line-height: 1.9;
    padding-left: 11px;
    position: relative;
  }
  .rec-list li::before {
    content: '✦';
    position: absolute;
    left: 0;
    top: 0;
    color: var(--dark);
    font-size: 10px;
  }
  .rec-list li b { color: var(--dark); font-weight: 500; }

  /* body-grid */
  .body-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }

  /* palette */
  .color-sub {
    font-family: 'Playfair Display', serif;
    font-size: 13px;
    font-weight: 700;
    color: var(--dark);
    margin: 16px 0 10px;
    letter-spacing: 0.4px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }
  .color-sub:first-child { margin-top: 0; }
  .swatch-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px 14px;
  }
  .swatch-item {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .swatch-chip {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    border: 1px solid rgba(0,0,0,0.1);
    box-shadow: inset 0 0 0 2px rgba(255,255,255,0.4);
    flex-shrink: 0;
  }
  .swatch-chip.strike {
    position: relative;
    opacity: 0.85;
  }
  .swatch-chip.strike::after {
    content: '';
    position: absolute;
    left: -3px; right: -3px; top: 50%;
    height: 1px;
    background: var(--dark);
    transform: rotate(-20deg);
  }
  .swatch-text { display: flex; flex-direction: column; line-height: 1.2; }
  .swatch-name {
    font-size: 12px;
    color: var(--dark);
    font-weight: 500;
  }
  .swatch-hex {
    font-family: 'EB Garamond', serif;
    font-size: 10.5px;
    color: var(--light);
    letter-spacing: 0.5px;
    margin-top: 2px;
  }

  /* lookbook */
  .lookbook-photos {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 12px;
  }
  .lookbook-photos img {
    width: 100%;
    height: auto;
    object-fit: contain;
    display: block;
    background: #ece8e2;
  }
  .photo-ph {
    aspect-ratio: 2/3;
    background: linear-gradient(160deg, #c8c4bc 0%, #a8a49c 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    color: #888;
    letter-spacing: 0.5px;
  }
  .look-caption { font-size: 11px; color: var(--mid); line-height: 1.75; margin-top: 7px; margin-bottom: 9px; word-break: keep-all; overflow-wrap: anywhere; }
  .look-caption b { color: var(--dark); font-weight: 600; margin-right: 4px; font-family: 'Playfair Display', serif; font-size: 12px; }

  /* summary */
  .summary-heading {
    font-family: 'Playfair Display', serif;
    font-size: 14px;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 9px;
  }
  .summary-text { font-size: 11.5px; color: var(--mid); line-height: 1.9; word-break: keep-all; overflow-wrap: anywhere; }
  .info-row, .bullets li, .rec-list li, .palette-item { word-break: keep-all; overflow-wrap: anywhere; }
  .summary-text strong { color: var(--dark); font-weight: 500; }

  /* footer */
  .footer {
    padding-top: 16px;
    font-family: 'EB Garamond', serif;
    font-style: italic;
    font-size: 14px;
    color: var(--mid);
    line-height: 1.7;
  }

  .right { text-align: right; }

  @page { size: A4 portrait; margin: 6mm; }
  @media print {
    .dl-bar { display: none !important; }
    html, body { background: #fff !important; padding: 0 !important; margin: 0 !important; }
    body { display: block !important; }
    .page {
      box-shadow: none !important;
      width: 100% !important;
      max-width: 100% !important;
      padding: 8mm 10mm !important;
    }
    .brand { font-size: 56px !important; }
    .tagline { font-size: 20px !important; }
    .subtitle { font-size: 13px !important; }
    .header { grid-template-columns: 1fr 210px !important; }
  }
</style>
</head>
<body>
<div class="dl-bar" style="position:fixed;top:16px;right:16px;z-index:9999;background:rgba(255,255,255,0.95);padding:8px 10px;border:1px solid #c8c2b8;border-radius:6px;box-shadow:0 2px 12px rgba(0,0,0,0.15);display:flex;gap:6px;">
  <button onclick="openInNewTab()" style="font-family:'Noto Sans KR',sans-serif;font-size:12px;padding:6px 12px;border:1px solid #1a1a1a;background:#fff;cursor:pointer;border-radius:2px;">🔗 새 탭</button>
  <button onclick="downloadPNG()" style="font-family:'Noto Sans KR',sans-serif;font-size:12px;padding:6px 12px;border:1px solid #1a1a1a;background:#fff;cursor:pointer;border-radius:2px;">📷 PNG</button>
  <button onclick="downloadPDF()" style="font-family:'Noto Sans KR',sans-serif;font-size:12px;padding:6px 12px;border:1px solid #1a1a1a;background:#1a1a1a;color:#fff;cursor:pointer;border-radius:2px;">📄 PDF</button>
</div>
<script>
function _target() { return document.querySelector('.page'); }
let _canvasCache = null;
async function _getCanvas() {
  if (_canvasCache) return _canvasCache;
  await _waitFonts();
  const el = _target();
  _canvasCache = await html2canvas(el, {
    scale: 3, useCORS: true, allowTaint: true,
    backgroundColor: '#f5f3ef',
    width: el.offsetWidth, height: el.offsetHeight,
    windowWidth: el.offsetWidth, windowHeight: el.offsetHeight,
    imageTimeout: 30000,
  });
  return _canvasCache;
}
function openInNewTab() {
  try {
    const html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const w = window.open(url, '_blank');
    if (!w) { alert('팝업 차단 해제 후 다시 시도하세요.'); return; }
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) {
    console.error(e);
    alert('새 탭 열기 실패: ' + (e && e.message ? e.message : e));
  }
}
function _stamp() { const d = new Date(); return d.getFullYear() + ('0'+(d.getMonth()+1)).slice(-2) + ('0'+d.getDate()).slice(-2) + '_' + ('0'+d.getHours()).slice(-2) + ('0'+d.getMinutes()).slice(-2); }
async function _waitFonts() {
  try { await document.fonts.ready; } catch(e) {}
}
async function downloadPNG() {
  try {
    const canvas = await _getCanvas();
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = 'sketch_report_' + _stamp() + '.png';
    document.body.appendChild(a); a.click(); a.remove();
  } catch (e) {
    console.error(e);
    alert('PNG 저장 실패: ' + (e && e.message ? e.message : e));
  }
}
async function downloadPDF() {
  try {
    const canvas = await _getCanvas();
    const el = _target();
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' });
    const pageW = pdf.internal.pageSize.getWidth();
    const pageH = pdf.internal.pageSize.getHeight();
    const margin = 6;
    const imgW = pageW - margin * 2;
    const usableH = pageH - margin * 2;

    const scale = canvas.width / el.offsetWidth;
    const pageCanvasH = Math.floor(canvas.width * (usableH / imgW));

    const elTop = el.getBoundingClientRect().top;
    const blocks = Array.from(el.querySelectorAll('.header, .grid-2, .footer'));
    const boundaries = [0];
    for (const b of blocks) {
      const rect = b.getBoundingClientRect();
      boundaries.push(Math.round((rect.bottom - elTop) * scale));
    }
    boundaries.push(canvas.height);
    const uniq = Array.from(new Set(boundaries)).sort((a, b) => a - b);

    let start = 0;
    while (start < canvas.height) {
      const maxEnd = start + pageCanvasH;
      let end = canvas.height;
      for (let i = uniq.length - 1; i >= 0; i--) {
        if (uniq[i] > start && uniq[i] <= maxEnd) { end = uniq[i]; break; }
      }
      if (end === canvas.height && end - start > pageCanvasH) end = start + pageCanvasH;

      const sliceH = end - start;
      const tmp = document.createElement('canvas');
      tmp.width = canvas.width;
      tmp.height = sliceH;
      const ctx = tmp.getContext('2d');
      ctx.fillStyle = '#f5f3ef';
      ctx.fillRect(0, 0, tmp.width, tmp.height);
      ctx.drawImage(canvas, 0, start, canvas.width, sliceH, 0, 0, canvas.width, sliceH);
      const sliceData = tmp.toDataURL('image/jpeg', 0.98);
      const sliceMm = sliceH * imgW / canvas.width;
      if (start > 0) pdf.addPage();
      pdf.addImage(sliceData, 'JPEG', margin, margin, imgW, sliceMm);
      start = end;
    }
    pdf.save('sketch_report_' + _stamp() + '.pdf');
  } catch (e) {
    console.error(e);
    alert('PDF 저장 실패: ' + (e && e.message ? e.message : e));
  }
}
</script>
<div class="page">

  <!-- HEADER -->
  <div class="header">
    <div>
      <div class="brand">Sketch.</div>
      <div class="tagline">Identity on the Street</div>
      <div class="subtitle">Identity Consulting Report</div>
    </div>
    <div class="header-photo-wrap">
      {% if before_image_b64 %}
        <img class="header-photo" src="data:image/png;base64,{{ before_image_b64 }}">
      {% else %}
        <div class="header-photo-ph">CLIENT PHOTO</div>
      {% endif %}
      {% if before_is_synthesized %}
        <div class="header-photo-caption">* 예상 이미지 (텍스트 묘사 기반 생성)</div>
      {% endif %}
    </div>
  </div>

  <!-- CLIENT + BEFORE -->
  <div class="grid-2 row-top row-bt">
    <div class="cell br">
      <div class="section-heading">Client Info</div>
      <div class="info-row">나이 : <span>{{ data.client_info.age }}</span></div>
      <div class="info-row">직업 : <span>{{ data.client_info.job }}</span></div>
      <div class="info-row">목표 이미지 : <span>{{ data.client_info.goal_image }}</span></div>
      <div class="info-row">현재 이미지 인상 : <span>{{ data.client_info.current_impression }}</span></div>
    </div>
    <div class="cell">
      <div class="section-heading">BEFORE</div>
      <div class="info-row">인상 : <span>{{ data.before.impression }}</span></div>
      <div class="info-row">분위기 : <span>{{ data.before.mood }}</span></div>
      <div class="info-row">존재감 : <span>{{ data.before.presence }}</span></div>
    </div>
  </div>

  <!-- ANALYSIS HEADER -->
  <div class="grid-2 row-bt">
    <div class="sec-head" style="border-right:1px solid var(--border);">Before Analysis</div>
    <div class="sec-head right">Key Recommendations</div>
  </div>

  <!-- BODY & STYLE + KEY REC -->
  <div class="grid-2 row-bt">
    <div class="cell br">
      <div class="col-title">Body &amp; Style Analysis</div>
      <div class="body-grid">
        <div>
          <div class="check">체형 분석</div>
          <ul class="bullets"><li>{{ data.body_style_analysis.body }}</li></ul>
          <div class="check">현재 스타일 문제점</div>
          <ul class="bullets"><li>{{ data.body_style_analysis.current_issue }}</li></ul>
        </div>
        <div>
          <div class="check">얼굴 인상 분석</div>
          <ul class="bullets"><li>{{ data.body_style_analysis.face }}</li></ul>
          <div class="check">이미지 보완 방향</div>
          <ul class="bullets"><li>{{ data.body_style_analysis.direction }}</li></ul>
        </div>
      </div>
    </div>
    <div class="cell">
      <ul class="rec-list">
        <li><b>상의 전략</b> — {{ data.key_recommendations.top }}</li>
        <li><b>하의 전략</b> — {{ data.key_recommendations.bottom }}</li>
        <li><b>실루엣 전략</b> — {{ data.key_recommendations.silhouette }}</li>
        <li><b>디테일 전략</b> — {{ data.key_recommendations.detail }}</li>
      </ul>
    </div>
  </div>

  <!-- AVOID + COLOR HEADER -->
  <div class="grid-2 row-bt">
    <div class="sec-head" style="border-right:1px solid var(--border);">Avoid These!</div>
    <div class="sec-head right">Color Recommendations</div>
  </div>

  <!-- AVOID + COLOR CONTENT -->
  <div class="grid-2 row-bt">
    <div class="cell br">
      <div class="body-grid">
        <div>
          <div class="check">피해야 할 핏</div>
          <ul class="bullets"><li>{{ data.avoid.fit }}</li></ul>
          <div class="check">피해야 할 무드</div>
          <ul class="bullets"><li>{{ data.avoid.mood }}</li></ul>
        </div>
        <div>
          <div class="check">피해야 할 컬러</div>
          <ul class="bullets"><li>{{ data.avoid.color }}</li></ul>
          <div class="check">비율 붕괴 요소</div>
          <ul class="bullets"><li>{{ data.avoid.ratio }}</li></ul>
        </div>
      </div>
    </div>
    <div class="cell">
      <div class="color-sub">Recommended Palette</div>
      <div class="swatch-grid">
        {% for c in data.colors.recommended %}
          {% set name = c.name if c is mapping else c %}
          {% set hex = c.hex if c is mapping else '#c8c2b8' %}
          <div class="swatch-item">
            <div class="swatch-chip" style="background: {{ hex }};"></div>
            <div class="swatch-text">
              <div class="swatch-name">{{ name }}</div>
              <div class="swatch-hex">{{ hex|upper }}</div>
            </div>
          </div>
        {% endfor %}
      </div>
      <div class="color-sub">Colors to Avoid</div>
      <div class="swatch-grid">
        {% for c in data.colors.avoid %}
          {% set name = c.name if c is mapping else c %}
          {% set hex = c.hex if c is mapping else '#c8c2b8' %}
          <div class="swatch-item">
            <div class="swatch-chip strike" style="background: {{ hex }};"></div>
            <div class="swatch-text">
              <div class="swatch-name">{{ name }}</div>
              <div class="swatch-hex">{{ hex|upper }}</div>
            </div>
          </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <!-- LOOKBOOK + SUMMARY HEADER -->
  <div class="grid-2 wide-left row-bt">
    <div class="sec-head" style="border-right:1px solid var(--border);">Style Lookbook</div>
    <div class="sec-head right">Sketch Styling Summary</div>
  </div>

  <!-- LOOKBOOK + SUMMARY -->
  <div class="grid-2 wide-left row-bt">
    <div class="cell br">
      {% set slot_n = (lookbook_b64|length) or (looks|length) or 1 %}
      <div class="lookbook-photos" style="grid-template-columns: repeat({{ slot_n }}, 1fr);">
        {% for img in lookbook_b64 %}<img src="data:image/png;base64,{{ img }}">{% endfor %}
        {% if not lookbook_b64 %}{% for _ in looks %}<div class="photo-ph">LOOK {{ loop.index }}</div>{% endfor %}{% endif %}
      </div>
      {% for desc in looks %}
        <div class="look-caption"><b>LOOK {{ loop.index }}.</b>{{ desc }}</div>
      {% endfor %}
    </div>
    <div class="cell">
      <div class="summary-heading">핵심 전략</div>
      <div class="summary-text">
        Keyword : <strong>{{ data.summary.keywords | join(" · ") }}</strong><br><br>
        {{ data.summary.strategy }}<br><br>
        <strong>Less but Stronger 전략 제안.</strong>
      </div>
    </div>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    "{{ data.final_comment }}"
  </div>

</div>
</body>
</html>
""")


def _img_to_b64(img: Optional[Image.Image]) -> Optional[str]:
    if img is None:
        return None
    buf = BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def render_html(data: dict,
                before_image: Optional[Image.Image] = None,
                lookbook_images: Optional[List[Image.Image]] = None,
                before_is_synthesized: bool = False) -> str:
    raw = data.get("lookbook")
    if isinstance(raw, list):
        looks = [s for s in raw if s]
    elif isinstance(raw, dict):
        looks = [v for v in raw.values() if v]
    else:
        looks = []
    images_b64 = [_img_to_b64(i) for i in (lookbook_images or []) if i is not None]
    return TEMPLATE.render(
        data=data,
        before_image_b64=_img_to_b64(before_image),
        lookbook_b64=images_b64,
        looks=looks,
        before_is_synthesized=before_is_synthesized,
    )
