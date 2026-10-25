# -*- coding: utf-8 -*-
"""Home page: a hero banner and one card per map, grouped by theme."""
import streamlit as st

import common as c
from menu import MAPS, SITE_TITLE

# accent colour on each card (by web address in menu.py) and the two groups shown
ACCENTS = {
    "greenspace": "#2E9E5B", "heat-islands": "#E8833A", "roads": "#E0482F",
    "transport": "#F2571E", "collapsed-buildings": "#B2182B",
    "alexandria-corniche": "#1565C0", "baltim": "#1E88A8", "ras-el-bar": "#3B6FB6",
    "port-said": "#29457F",
}
GROUPS = [
    ("مدينة الإسكندرية", "البيئة العمرانية والطرق والمواصلات والسلامة الإنشائية",
     ["greenspace", "heat-islands", "roads", "transport", "collapsed-buildings"]),
    ("الكورنيش والشواطئ", "استخدامات الواجهات البحرية وحق الوصول إلى البحر ورؤيته",
     ["alexandria-corniche", "baltim", "ras-el-bar", "port-said"]),
]
BY_URL = {m[3]: m for m in MAPS}
ACCENT_CSS = "".join(f".st-key-card_{u.replace('-', '_')} {{ --accent: {col}; }}" for u, col in ACCENTS.items())

st.markdown(f"""
<style>
.hero {{ background: linear-gradient(120deg, {c.NAVY} 0%, {c.BLUE} 70%, #3D8FE0 100%);
    border-radius: 18px; padding: 2.2rem 2.4rem 1.9rem; color: #FFFFFF; margin: 0.4rem 0 1.6rem;
    box-shadow: 0 10px 30px rgba(11,46,89,0.22); position: relative; overflow: hidden; }}
.hero::after {{ content: "🗺️"; position: absolute; left: 2rem; top: 50%; transform: translateY(-50%);
    font-size: 6.5rem; opacity: 0.16; }}
.hero h1 {{ color: #FFFFFF !important; font-size: 2rem; font-weight: 700; margin: 0 0 0.4rem; padding: 0; }}
.hero p {{ color: #DCE9F8 !important; font-size: 1.02rem; margin: 0 0 1.2rem; max-width: 46rem; }}
.chips {{ display: flex; gap: 0.6rem; flex-wrap: wrap; }}
.chip {{ background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.28);
    border-radius: 999px; padding: 0.3rem 0.95rem; font-size: 0.9rem; font-weight: 600; color: #FFFFFF; }}
.chip b {{ font-size: 1.05rem; margin-left: 0.3rem; }}

.group-head {{ display: flex; align-items: baseline; gap: 0.8rem; margin: 1.4rem 0 0.9rem;
    padding-bottom: 0.5rem; border-bottom: 2px solid {c.BORDER_BLUE}; }}
.group-head h3 {{ color: {c.NAVY} !important; font-size: 1.3rem; margin: 0; padding: 0; font-weight: 700; }}
.group-head span {{ color: #6B7280; font-size: 0.92rem; }}

/* cards */
div[class*="st-key-card_"] {{ background: #FFFFFF; border: 1px solid {c.BORDER_BLUE} !important;
    border-radius: 16px !important; padding: 1.15rem 1.2rem 1rem !important; height: 100%;
    box-shadow: 0 2px 8px rgba(11,46,89,0.06); transition: transform .18s ease, box-shadow .18s ease;
    border-top: 5px solid var(--accent) !important; gap: 0.7rem; }}
div[class*="st-key-card_"]:hover {{ transform: translateY(-4px);
    box-shadow: 0 12px 26px rgba(11,46,89,0.15); }}
.card-top {{ display: flex; align-items: center; gap: 0.8rem; }}
.card-icon {{ width: 3rem; height: 3rem; border-radius: 14px; display: flex; align-items: center;
    justify-content: center; font-size: 1.55rem; flex: none; }}
.card-title {{ color: {c.NAVY}; font-weight: 700; font-size: 1.08rem; line-height: 1.4; }}
.card-desc {{ color: #4B5563; font-size: 0.92rem; line-height: 1.75; min-height: 3.3rem; margin: 0; }}

/* the "open map" button */
div[class*="st-key-card_"] [data-testid="stPageLink"] a {{
    background: linear-gradient(90deg, {c.NAVY}, {c.BLUE}); border-radius: 999px;
    justify-content: center; padding: 0.5rem 1rem; transition: filter .15s ease, box-shadow .15s ease;
    box-shadow: 0 3px 10px rgba(21,101,192,0.30); }}
div[class*="st-key-card_"] [data-testid="stPageLink"] a:hover {{
    filter: brightness(1.15); box-shadow: 0 6px 16px rgba(21,101,192,0.40); background-color: transparent; }}
div[class*="st-key-card_"] [data-testid="stPageLink"] a p,
div[class*="st-key-card_"] [data-testid="stPageLink"] a span {{ color: #FFFFFF !important; font-weight: 700;
    font-size: 0.98rem; }}

.tips {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 2rem 0 0.6rem; }}
.tip {{ flex: 1 1 14rem; background: {c.LIGHT_BLUE}; border-radius: 12px; padding: 0.8rem 1rem;
    color: {c.NAVY}; font-size: 0.92rem; line-height: 1.7; }}
.tip b {{ display: block; font-size: 1rem; margin-bottom: 0.15rem; }}
{ACCENT_CSS}
@media (max-width: 700px) {{
  .hero {{ padding: 1.5rem 1.3rem; }} .hero h1 {{ font-size: 1.5rem; }} .hero::after {{ display: none; }}
}}
</style>
<div class="hero">
  <h1>{SITE_TITLE}</h1>
  <p>منصة خرائط تفاعلية لرصد البيئة العمرانية في الإسكندرية والواجهات البحرية في مدن ساحل البحر المتوسط.
     اختر خريطة لاستكشاف بياناتها ومؤشراتها ورسومها البيانية.</p>
  <div class="chips">
    <span class="chip"><b>{len(MAPS)}</b> خرائط تفاعلية</span>
    <span class="chip"><b>4</b> محافظات</span>
    <span class="chip"><b>4</b> واجهات بحرية</span>
  </div>
</div>
""", unsafe_allow_html=True)

for title, sub, urls in GROUPS:
    st.markdown(f'<div class="group-head"><h3>{title}</h3><span>{sub}</span></div>', unsafe_allow_html=True)
    per_row = 3
    for start in range(0, len(urls), per_row):
        cols = st.columns(per_row, gap="large")
        for col, url in zip(cols, urls[start:start + per_row]):
            file, name, icon, _u, desc = BY_URL[url]
            accent = ACCENTS.get(url, c.BLUE)
            with col:
                with st.container(key=f"card_{url.replace('-', '_')}"):
                    st.markdown(
                        f'<div class="card-top"><div class="card-icon" style="background:{accent}1F">{icon}</div>'
                        f'<div class="card-title">{name}</div></div><p class="card-desc">{desc}</p>',
                        unsafe_allow_html=True)
                    st.page_link(file, label="فتح الخريطة  ←", use_container_width=True)

st.markdown("""
<div class="tips">
  <div class="tip"><b>🧭 التنقل</b>استخدم القائمة أعلى الصفحة للانتقال بين الخرائط في أي وقت.</div>
  <div class="tip"><b>🗂️ مفتاح الخريطة</b>فعّل الطبقات أو أخفها من المفتاح داخل الخريطة دون إعادة تحميلها.</div>
  <div class="tip"><b>👆 التفاصيل</b>انقر على أي عنصر في الخريطة لعرض بياناته وصوره إن وجدت.</div>
</div>
""", unsafe_allow_html=True)
