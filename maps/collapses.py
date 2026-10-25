# -*- coding: utf-8 -*-
"""حصر لعقارات الإسكندرية المنهارة (يناير 2021: يوليو 2023) — data in data/collapses/"""
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import common as c

APP = "collapses"
FILE = "Alexandria_collapsed_buildings.geojson"
TITLE = "حصر لعقارات الإسكندرية المنهارة (يناير 2021: يوليو 2023)"
DATE_COL = "تاريخ الانهيار"
TYPE_COL = "نوع الانهيار"
OCC_COL = "حالة الإشغال"
DEATH_COL = "عدد الوفيات"
INJ_COL = "عدد المصابين"
TOTAL_COL = "إجمالي الضحايا"
DEMO_COL = "قرار هدم سابق"
RENO_COL = "قرار ترميم سابق"
POPUP_COLS = [DATE_COL, TYPE_COL, OCC_COL, DEATH_COL, INJ_COL, TOTAL_COL, DEMO_COL, RENO_COL]
# dot colour/size by total casualties: (lowest, highest, colour, radius px, legend label)
CLASSES = [
    (0, 0, "#9FB3C8", 5, "بدون ضحايا"),
    (1, 2, "#FDB863", 7, "1 - 2"),
    (3, 5, "#F46D43", 9, "3 - 5"),
    (6, 9999, "#B2182B", 12, "6 فأكثر"),
]
# simpler groups of the many collapse-type spellings (chart only)
TYPE_GROUPS = {
    "جزئي": "جزئي", "كلي": "كلي", "نصف العقار": "نصف العقار",
    "شرفة": "شرفات", "شرفات": "شرفات", "شرفتين": "شرفات", "3 شرفات": "شرفات", "4 شرفات": "شرفات",
    "سقف": "أسقف", "أسقف": "أسقف", "الأسقف": "أسقف", "سقف حجرة": "أسقف",
    "سلم": "سلم", "تصدع": "تصدع", "داخلي": "داخلي",
    "أجزاء متهالكة": "أجزاء متهالكة أو خطرة", "أجزاء خطرة": "أجزاء متهالكة أو خطرة",
}
MONTHS_AR = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
             7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}


def casualty_class(total):
    for i, (lo, hi, *_r) in enumerate(CLASSES):
        if lo <= total <= hi:
            return i
    return len(CLASSES) - 1


def date_ar(d):
    return f"{d.day} {MONTHS_AR[d.month]} {d.year}" if pd.notna(d) else "—"


@st.cache_data(show_spinner=False)
def load():
    gdf = c.read_geo(c.data_path(APP, FILE))
    for col in [DEATH_COL, INJ_COL]:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0).astype(int)
    gdf[TOTAL_COL] = gdf[DEATH_COL] + gdf[INJ_COL]
    gdf["class"] = gdf[TOTAL_COL].apply(casualty_class)
    gdf["date"] = pd.to_datetime(gdf[DATE_COL], errors="coerce")
    gdf["year"] = gdf["date"].dt.year
    gdf["type_group"] = gdf[TYPE_COL].map(TYPE_GROUPS).fillna("أخرى")
    gdf.loc[gdf[TYPE_COL].isna(), "type_group"] = "غير محدد"
    popups, tips = [], []
    for _, r in gdf.iterrows():
        cls = CLASSES[int(r["class"])]
        rows = [(col, date_ar(r["date"]) if col == DATE_COL else c.fmt(r.get(col))) for col in POPUP_COLS]
        popups.append(c.popup_html(f"عقار منهار — {date_ar(r['date'])}", f"الضحايا: {cls[4]}", cls[2],
                                   rows, badge_text=c.text_on(cls[2])))
        tips.append(c.tip_html(date_ar(r["date"]), f"الوفيات: {r[DEATH_COL]} — المصابين: {r[INJ_COL]}"))
    gdf["popup"], gdf["tip"] = popups, tips
    return gdf.reset_index(drop=True)


@st.cache_resource(max_entries=c.MAP_CACHE_ENTRIES, show_spinner=False)
def build_map(years):
    all_data = load()
    data = all_data[all_data["year"].isin(years)]
    m = c.new_map()
    # low-casualty dots first so the most serious sit on top
    for i, (_lo, _hi, color, radius, label) in enumerate(CLASSES):
        sub = data[data["class"] == i]
        fg = c.group(m, c.lg_label(label, c.lg_dot(color, min(2 * radius, 18)), len(sub)))
        c.add_geojson(fg, c.to_geojson(sub, ["popup", "tip"]),
                      lambda _f, color=color, radius=radius: {
                          "fillColor": color, "fillOpacity": c.FILL_OPACITY, "color": "#FFFFFF",
                          "weight": 1.5, "opacity": 1, "radius": radius},
                      weight_hover=3, marker=folium.CircleMarker(radius=radius, fill=True))
    return c.finish_map(m, all_data.total_bounds, title="إجمالي الضحايا (وفيات + مصابين)", padding=20)


# ---------------------------------------------------------------- page
c.require_files(APP, [FILE])
all_data = load()
years = sorted(int(y) for y in all_data["year"].dropna().unique())
with st.sidebar:
    st.header("إعدادات الخريطة")
    chosen = st.multiselect("السنوات", years, default=years)
data = all_data[all_data["year"].isin(chosen)]

c.page_title(TITLE, "🏚️")
n = len(data)
with_victims = int((data[TOTAL_COL] > 0).sum())
k = st.columns(5)
k[0].metric("عدد العقارات المنهارة", f"{n}")
k[1].metric("إجمالي الوفيات", f"{int(data[DEATH_COL].sum())}")
k[2].metric("إجمالي المصابين", f"{int(data[INJ_COL].sum())}")
k[3].metric("حالات بها ضحايا", f"{with_victims}",
            f"{100 * with_victims / n:.0f}% من الحالات" if n else None, delta_color="off")
k[4].metric("عقارات صدر لها قرار هدم سابق", f"{int(data[DEMO_COL].notna().sum())}")
c.metric_cards()

if data.empty:
    st.info("لا توجد حالات مطابقة للاختيارات الحالية.")
c.show_map(build_map(tuple(sorted(chosen))), key="collapses_map")
st.caption("انقر على أي نقطة في الخريطة لعرض تفاصيل الانهيار. السنوات من القائمة الجانبية (») ومفتاح الخريطة لإظهار الفئات أو إخفائها.")

with st.expander("عدد حالات الانهيار كل ربع سنة"):
    q = data.dropna(subset=["date"]).copy()
    q["quarter"] = q["date"].dt.to_period("Q")
    periods = pd.period_range(all_data["date"].min(), all_data["date"].max(), freq="Q")
    labels = [f"الربع {p.quarter} — {p.year}" for p in periods]
    counts = q.groupby(["quarter", "class"]).size().unstack(fill_value=0).reindex(periods, fill_value=0)
    fig = go.Figure()
    for i, (_lo, _hi, color, _r, label) in enumerate(CLASSES):
        if i in counts.columns:
            fig.add_trace(go.Bar(name=label, x=labels, y=counts[i], marker_color=color,
                                 marker_line_color=c.NAVY, marker_line_width=0.4,
                                 hovertemplate="<b>%{x}</b><br>" + label + ": %{y}<extra></extra>"))
    c.bar_layout(fig, 380, barmode="stack", yaxis_title="عدد الحالات", xaxis=dict(autorange="reversed"),
                 legend=dict(orientation="h", y=1.12, x=1, xanchor="right", title_text="إجمالي الضحايا: "))
    c.show_chart(fig)

with st.expander("الوفيات والمصابين حسب السنة"):
    by_year = data.groupby("year")[[DEATH_COL, INJ_COL]].sum().reindex(years, fill_value=0)
    fig = go.Figure()
    for col, color in [(DEATH_COL, "#B2182B"), (INJ_COL, "#F46D43")]:
        fig.add_trace(go.Bar(name=col.replace("عدد ", ""), x=[str(y) for y in by_year.index],
                             y=by_year[col], marker_color=color, text=by_year[col], textposition="outside",
                             hovertemplate="<b>%{x}</b><br>" + col + ": %{y}<extra></extra>"))
    c.bar_layout(fig, 360, barmode="group", yaxis_title="عدد الأفراد",
                 xaxis=dict(autorange="reversed", type="category"),
                 legend=dict(orientation="h", y=1.12, x=1, xanchor="right"))
    c.show_chart(fig)

with st.expander("حالات الانهيار حسب نوع الانهيار"):
    by_type = data["type_group"].value_counts().sort_values()
    fig = go.Figure(go.Bar(x=by_type.values, y=[t + "  " for t in by_type.index], orientation="h",
                           marker_color=c.BLUE, text=by_type.values, textposition="outside",
                           hovertemplate="<b>%{y}</b><br>%{x} حالة<extra></extra>"))
    c.bar_layout(fig, max(320, 30 * len(by_type)), xaxis_title="عدد الحالات", yaxis=dict(side="right"))
    c.show_chart(fig)

with st.expander("جدول الحالات الكامل"):
    st.dataframe(data.sort_values("date", ascending=False)[POPUP_COLS], hide_index=True,
                 use_container_width=True)
