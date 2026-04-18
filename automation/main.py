"""Streamlit app: Sketch Identity Consulting Report automation."""
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / f"app_{datetime.now():%Y%m%d}.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("sketch.main")

from modules.ai_engine import GeminiEngine
from modules.renderer import render_html
from modules.rate_limit import check_and_increment, peek

ROOT = Path(__file__).parent.parent
GEN_DIR = ROOT / "generated_image"

st.set_page_config(page_title="Sketch Identity Report", layout="wide")

def _check_password() -> bool:
    try:
        expected = st.secrets.get("APP_PASSWORD")
    except Exception:
        expected = None
    if not expected:
        import os
        expected = os.getenv("APP_PASSWORD")
    if not expected:
        return True  # no password configured → open access
    if st.session_state.get("pw_ok"):
        return True
    st.title("🔒 Sketch Report")
    pw = st.text_input("비밀번호", type="password")
    if st.button("입장"):
        if pw == expected:
            st.session_state["pw_ok"] = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    return False

if not _check_password():
    st.stop()

st.title("Sketch. Identity Consulting Report 자동화")

mode = st.radio("입력 모드", ["1) 전신샷 업로드", "2) 텍스트 폼만"], horizontal=True)

with st.sidebar:
    st.header("Client Info")
    age = st.text_input("나이", "21")
    job = st.text_input("직업", "대학생")
    goal = st.text_input("추구미 키워드", "청순")
    n_looks = st.slider("룩북 이미지 수", 1, 3, 3)

before_file = None
ref_files = []
extra_text = ""

if mode.startswith("1"):
    before_file = st.file_uploader("BEFORE 전신 사진", type=["jpg", "jpeg", "png"])
    ref_files = st.file_uploader("추구미 이미지 (최대 2장)",
                                 type=["jpg", "jpeg", "png"],
                                 accept_multiple_files=True)
else:
    extra_text = st.text_area("외형/선호 상세 텍스트",
                              height=220,
                              placeholder="예) 핑크/붉은기 있음\n홍조 트러블 심함\n눈동자 다크 브라운\n...")

def _client_ip() -> str:
    try:
        h = dict(st.context.headers)
        fwd = h.get("X-Forwarded-For") or h.get("x-forwarded-for") or ""
        if fwd:
            return fwd.split(",")[0].strip()
        return h.get("X-Real-Ip") or h.get("x-real-ip") or "unknown"
    except Exception:
        return "unknown"

client_ip = _client_ip()
used, daily_limit = peek(client_ip)
st.caption(f"오늘 생성 사용량: {used} / {daily_limit} (IP 기준)")

run = st.button("리포트 생성", type="primary", disabled=(used >= daily_limit))

if run:
    allowed, used, daily_limit = check_and_increment(client_ip)
    if not allowed:
        st.error(f"이 IP의 오늘 생성 한도({daily_limit}회)를 모두 사용했습니다. 내일 다시 시도해주세요.")
        st.stop()
    logger.info("=== run clicked: ip=%s mode=%s age=%s job=%s goal=%s used=%d/%d ===",
                client_ip, mode, age, job, goal, used, daily_limit)
    if mode.startswith("1") and not before_file:
        st.error("전신샷을 업로드해주세요.")
        st.stop()
    if mode.startswith("2") and not extra_text.strip():
        st.error("외형 상세 텍스트를 입력해주세요.")
        st.stop()

    def _downscale(img, max_side=1024):
        if img is None:
            return None
        w, h = img.size
        if max(w, h) <= max_side:
            return img
        scale = max_side / max(w, h)
        return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    engine = GeminiEngine()
    before_img = _downscale(Image.open(before_file)) if before_file else None
    refs = [_downscale(Image.open(f)) for f in (ref_files or [])][:2]

    with st.spinner("리포트 텍스트 생성 중..."):
        try:
            data = engine.generate_report(age, job, goal,
                                          before_image=before_img,
                                          ref_images=refs,
                                          extra_text=extra_text)
        except Exception as e:
            logger.exception("report generation failed")
            st.exception(e)
            st.stop()

    if before_img is None and extra_text.strip():
        with st.spinner("외형 묘사 기반 BEFORE 이미지 생성 중..."):
            try:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                before_path = GEN_DIR / f"before_{ts}.png"
                p = engine.generate_before_image(age, job, goal, extra_text, before_path)
                if p:
                    before_img = _downscale(Image.open(p))
            except Exception as e:
                logger.exception("before image generation failed")
                st.warning(f"BEFORE 이미지 생성 실패: {e}")

    lookbook = [None] * n_looks
    if before_img is not None:
        with st.spinner(f"룩북 이미지 {n_looks}장 병렬 생성 중..."):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            def _gen(i):
                out = GEN_DIR / f"look_{ts}_{i+1}.png"
                return i, engine.generate_styling_image(age, goal, before_img, out, look_index=i)

            with ThreadPoolExecutor(max_workers=n_looks) as ex:
                for fut in [ex.submit(_gen, i) for i in range(n_looks)]:
                    try:
                        idx, path = fut.result()
                        if path:
                            lookbook[idx] = Image.open(path)
                    except Exception as e:
                        logger.exception("lookbook generation failed")
                        st.warning(f"룩북 생성 실패: {e}")
        lookbook = [img for img in lookbook if img is not None]

    html = render_html(data, before_image=before_img, lookbook_images=lookbook)
    if st.session_state.get("html") != html:
        st.session_state.pop("png_bytes", None)
        st.session_state.pop("pdf_bytes", None)
    st.session_state["html"] = html
    st.session_state["data"] = data
    st.session_state["before_img"] = before_img
    st.session_state["lookbook"] = lookbook
    st.session_state["stamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")


if "html" in st.session_state:
    html = st.session_state["html"]
    data = st.session_state["data"]
    stamp = st.session_state["stamp"]

    st.success("리포트 생성 완료")

    with st.expander("✏️ 수정하기 (텍스트 · 이미지)", expanded=False):
        edited = {
            "client_info": {}, "before": {}, "body_style_analysis": {},
            "key_recommendations": {}, "avoid": {}, "colors": {}, "summary": {},
        }
        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("**Client Info**")
            for k, lbl in [("age", "나이"), ("job", "직업"),
                           ("goal_image", "목표 이미지"), ("current_impression", "현재 인상")]:
                edited["client_info"][k] = st.text_input(lbl, data["client_info"].get(k, ""), key=f"ci_{k}")
            st.markdown("**Before**")
            for k, lbl in [("impression", "인상"), ("mood", "분위기"), ("presence", "존재감")]:
                edited["before"][k] = st.text_input(lbl, data["before"].get(k, ""), key=f"bf_{k}")
            st.markdown("**Body & Style**")
            for k, lbl in [("body", "체형"), ("face", "얼굴 인상"),
                           ("current_issue", "현재 문제점"), ("direction", "보완 방향")]:
                edited["body_style_analysis"][k] = st.text_area(lbl, data["body_style_analysis"].get(k, ""), key=f"bs_{k}", height=70)
            st.markdown("**Key Recommendations**")
            for k, lbl in [("top", "상의"), ("bottom", "하의"),
                           ("silhouette", "실루엣"), ("detail", "디테일")]:
                edited["key_recommendations"][k] = st.text_area(lbl, data["key_recommendations"].get(k, ""), key=f"kr_{k}", height=70)
        with ec2:
            st.markdown("**Avoid**")
            for k, lbl in [("fit", "핏"), ("color", "컬러"),
                           ("mood", "무드"), ("ratio", "비율 붕괴")]:
                edited["avoid"][k] = st.text_area(lbl, data["avoid"].get(k, ""), key=f"av_{k}", height=70)
            st.markdown("**Colors** (형식: `이름 #HEX`, 콤마로 구분)")

            def _fmt_colors(items):
                out = []
                for c in items or []:
                    if isinstance(c, dict):
                        out.append(f"{c.get('name','')} {c.get('hex','')}".strip())
                    else:
                        out.append(str(c))
                return ", ".join(out)

            def _parse_colors(txt):
                result = []
                for raw in txt.split(","):
                    raw = raw.strip()
                    if not raw:
                        continue
                    parts = raw.rsplit(" ", 1)
                    if len(parts) == 2 and parts[1].startswith("#"):
                        result.append({"name": parts[0].strip(), "hex": parts[1].strip()})
                    else:
                        result.append({"name": raw, "hex": "#c8c2b8"})
                return result

            rec_txt = st.text_input("추천", _fmt_colors(data["colors"].get("recommended", [])), key="col_rec")
            avo_txt = st.text_input("피할 색", _fmt_colors(data["colors"].get("avoid", [])), key="col_avo")
            edited["colors"]["recommended"] = _parse_colors(rec_txt)
            edited["colors"]["avoid"] = _parse_colors(avo_txt)
            st.markdown("**Lookbook Descriptions**")
            raw_looks = data.get("lookbook") if isinstance(data.get("lookbook"), list) else []
            edited_looks = []
            for i in range(max(len(raw_looks), len(st.session_state.get("lookbook") or []))):
                edited_looks.append(st.text_area(f"LOOK {i+1}", raw_looks[i] if i < len(raw_looks) else "", key=f"lk_{i}", height=70))
            edited["lookbook"] = [s for s in edited_looks if s]
            st.markdown("**Summary**")
            kw_txt = st.text_input("키워드 (콤마 구분)", " · ".join(data["summary"].get("keywords", [])).replace(" · ", ", "), key="sm_kw")
            edited["summary"]["keywords"] = [x.strip() for x in kw_txt.split(",") if x.strip()]
            edited["summary"]["strategy"] = st.text_area("전략", data["summary"].get("strategy", ""), key="sm_st", height=80)
            edited["final_comment"] = st.text_area("Final Comment", data.get("final_comment", ""), key="fc", height=60)

        st.markdown("---")
        st.markdown("**BEFORE 사진 교체**")
        new_before = st.file_uploader("BEFORE", type=["jpg", "jpeg", "png"], key="edit_before", label_visibility="collapsed")

        st.markdown("**룩북 이미지 재생성** (프롬프트 입력 후 재생성 버튼)")
        existing_lb = st.session_state.get("lookbook") or []
        n_slots = max(len(existing_lb), 3)
        lb_cols = st.columns(n_slots)
        for i in range(n_slots):
            with lb_cols[i]:
                if i < len(existing_lb) and existing_lb[i] is not None:
                    st.image(existing_lb[i], caption=f"LOOK {i+1}", width="stretch")
                else:
                    st.markdown(f"LOOK {i+1} (없음)")
                p = st.text_area(f"추가 지시 (LOOK {i+1})", key=f"prompt_lb_{i}",
                                 placeholder="예) 화이트 셔츠 + 연청 데님, 골드 액세서리",
                                 height=80)
                if st.button(f"LOOK {i+1} 재생성", key=f"regen_lb_{i}"):
                    bf = st.session_state.get("before_img")
                    if bf is None:
                        st.error("BEFORE 사진이 없어 재생성 불가")
                    else:
                        with st.spinner(f"LOOK {i+1} 재생성 중…"):
                            try:
                                engine = GeminiEngine()
                                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                out = GEN_DIR / f"look_{ts}_regen_{i+1}.png"
                                path = engine.generate_styling_image(
                                    age, goal, bf, out,
                                    look_index=i, custom_prompt=p)
                                if path:
                                    lb2 = list(existing_lb)
                                    while len(lb2) <= i:
                                        lb2.append(None)
                                    lb2[i] = Image.open(path)
                                    st.session_state["lookbook"] = [x for x in lb2 if x is not None]
                                    new_html = render_html(data, before_image=bf,
                                                           lookbook_images=st.session_state["lookbook"])
                                    st.session_state["html"] = new_html
                                    st.session_state.pop("png_bytes", None)
                                    st.session_state.pop("pdf_bytes", None)
                                    st.rerun()
                            except Exception as e:
                                logger.exception("regen lb %d failed", i + 1)
                                st.error(f"재생성 실패: {e}")

        if st.button("수정 적용", type="primary", key="apply_edit"):
            new_data = {**data, **edited}
            before_img2 = Image.open(new_before) if new_before else st.session_state.get("before_img")
            new_html = render_html(new_data, before_image=before_img2,
                                   lookbook_images=st.session_state.get("lookbook") or [])
            st.session_state["html"] = new_html
            st.session_state["data"] = new_data
            st.session_state["before_img"] = before_img2
            st.session_state.pop("png_bytes", None)
            st.session_state.pop("pdf_bytes", None)
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["미리보기", "JSON", "HTML"])
    with tab1:
        st.components.v1.html(html, height=1700, scrolling=True)
    with tab2:
        st.json(data)
    with tab3:
        st.code(html, language="html")

    st.download_button("HTML 다운로드",
                       data=html.encode("utf-8"),
                       file_name=f"sketch_report_{stamp}.html",
                       mime="text/html",
                       key="html_dl")
    st.caption("📷 PNG / 📄 PDF 저장: 위 미리보기 우측 상단 버튼 사용. 잘림이 있으면 HTML을 다운로드해 브라우저에서 직접 열어 저장하세요.")
