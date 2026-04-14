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
    width: 900px;
    padding: 48px 52px 40px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.12);
  }

  /* HEADER */
  .header {
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 32px;
    margin-bottom: 28px;
    align-items: start;
  }
  .brand {
    font-family: 'Playfair Display', serif;
    font-size: 80px;
    font-weight: 900;
    letter-spacing: -2px;
    line-height: 1;
    color: var(--dark);
  }
  .tagline {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 26px;
    font-weight: 700;
    color: var(--dark);
    margin-top: 4px;
    letter-spacing: 0.5px;
  }
  .subtitle {
    font-family: 'EB Garamond', serif;
    font-size: 17px;
    color: var(--mid);
    margin-top: 6px;
    letter-spacing: 2px;
  }
  .header-photo, .header-photo-ph {
    width: 100%;
    aspect-ratio: 3/4;
    object-fit: cover;
    object-position: top center;
    display: block;
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
  .cell { padding: 20px 24px 24px; }
  .cell.br { border-right: 1px solid var(--border); }
  .row-top { border-top: 1px solid var(--border); }
  .row-bt { border-bottom: 1px solid var(--border); }

  /* SECTION HEADINGS */
  .sec-head {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--dark);
    padding: 16px 24px;
  }
  .sec-head.right { text-align: right; }
  .section-heading {
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 14px;
    letter-spacing: 0.3px;
  }
  .col-title {
    font-family: 'Playfair Display', serif;
    font-size: 16px;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 14px;
  }

  .info-row {
    font-size: 13px;
    color: var(--mid);
    line-height: 2;
  }
  .info-row span {
    color: var(--dark);
    font-weight: 500;
  }

  /* check + bullets */
  .check {
    font-size: 12.5px;
    font-weight: 500;
    color: var(--dark);
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .check::before { content: '✓'; font-size: 12px; color: var(--dark); }

  .bullets { list-style: none; padding: 0; margin-bottom: 12px; }
  .bullets li {
    font-size: 12px;
    color: var(--mid);
    line-height: 1.9;
    padding-left: 10px;
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
    font-size: 12.5px;
    color: var(--mid);
    line-height: 2;
    padding-left: 12px;
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
    font-size: 12px;
    font-weight: 500;
    color: var(--dark);
    margin: 14px 0 8px;
    letter-spacing: 0.3px;
  }
  .color-sub:first-child { margin-top: 0; }
  .palette-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px 0;
  }
  .palette-item {
    font-size: 12px;
    color: var(--mid);
    line-height: 2;
    padding-left: 12px;
    position: relative;
  }
  .palette-item::before {
    content: '✦';
    position: absolute;
    left: 0;
    color: var(--dark);
    font-size: 10px;
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
    aspect-ratio: 2/3;
    object-fit: cover;
    display: block;
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
  .look-caption { font-size: 12px; color: var(--mid); line-height: 1.8; margin-top: 8px; }
  .look-caption b { color: var(--dark); font-weight: 600; margin-right: 4px; font-family: 'Playfair Display', serif; font-size: 13px; }

  /* summary */
  .summary-heading {
    font-family: 'Playfair Display', serif;
    font-size: 15px;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 10px;
  }
  .summary-text { font-size: 12.5px; color: var(--mid); line-height: 2; }
  .summary-text strong { color: var(--dark); font-weight: 500; }

  /* footer */
  .footer {
    padding-top: 18px;
    font-family: 'EB Garamond', serif;
    font-style: italic;
    font-size: 15px;
    color: var(--mid);
    line-height: 1.7;
  }

  .right { text-align: right; }
</style>
</head>
<body>
<div class="dl-bar" style="position:sticky;top:0;z-index:9999;background:#e8e4de;padding:8px 16px;border-bottom:1px solid #c8c2b8;display:flex;gap:8px;justify-content:flex-end;">
  <button onclick="downloadPNG()" style="font-family:'Noto Sans KR',sans-serif;font-size:12px;padding:6px 14px;border:1px solid #1a1a1a;background:#fff;cursor:pointer;border-radius:2px;">📷 PNG 저장</button>
  <button onclick="downloadPDF()" style="font-family:'Noto Sans KR',sans-serif;font-size:12px;padding:6px 14px;border:1px solid #1a1a1a;background:#1a1a1a;color:#fff;cursor:pointer;border-radius:2px;">📄 PDF 저장</button>
</div>
<script>
function _target() { return document.querySelector('.page'); }
function _stamp() { const d = new Date(); return d.getFullYear() + ('0'+(d.getMonth()+1)).slice(-2) + ('0'+d.getDate()).slice(-2) + '_' + ('0'+d.getHours()).slice(-2) + ('0'+d.getMinutes()).slice(-2); }
function downloadPNG() {
  html2canvas(_target(), {scale: 2, useCORS: true, backgroundColor: '#f5f3ef'}).then(canvas => {
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = 'sketch_report_' + _stamp() + '.png';
    a.click();
  });
}
function downloadPDF() {
  const opt = {
    margin: 8,
    filename: 'sketch_report_' + _stamp() + '.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, backgroundColor: '#f5f3ef' },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };
  html2pdf().set(opt).from(_target()).save();
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
    {% if before_image_b64 %}
      <img class="header-photo" src="data:image/png;base64,{{ before_image_b64 }}">
    {% else %}
      <div class="header-photo-ph">CLIENT PHOTO</div>
    {% endif %}
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
      <div class="color-sub">Recommended palette</div>
      <div class="palette-grid">
        {% for c in data.colors.recommended %}<div class="palette-item">{{ c }}</div>{% endfor %}
      </div>
      <div class="color-sub">Colors to avoid</div>
      <ul class="rec-list">
        {% for c in data.colors.avoid %}<li>{{ c }}</li>{% endfor %}
      </ul>
    </div>
  </div>

  <!-- LOOKBOOK + SUMMARY HEADER -->
  <div class="grid-2 row-bt">
    <div class="sec-head" style="border-right:1px solid var(--border);">Style Lookbook</div>
    <div class="sec-head right">Sketch Styling Summary</div>
  </div>

  <!-- LOOKBOOK + SUMMARY -->
  <div class="grid-2 row-bt">
    <div class="cell br">
      <div class="lookbook-photos">
        {% for img in lookbook_b64 %}<img src="data:image/png;base64,{{ img }}">{% endfor %}
        {% for _ in range(3 - lookbook_b64|length) %}<div class="photo-ph">LOOK {{ loop.index + lookbook_b64|length }}</div>{% endfor %}
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
                lookbook_images: Optional[List[Image.Image]] = None) -> str:
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
    )
