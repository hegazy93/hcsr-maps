# -*- coding: utf-8 -*-
"""نصيب الفرد من المساحات الخضراء — محافظة الإسكندرية — data in data/greenspace/"""
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import common as c

APP = "greenspace"
FILE = "Greenspaces_Alexandria.geojson"
TITLE = "نصيب الفرد من المساحات الخضراء — محافظة الإسكندرية"
VALUE_COL = "نصيب"
NAME_COL = "إسم_ا"
# the shapefile export cut the column names short; edit labels/units here if needed
COLUMN_LABELS = {
    "إسم_ا": "اسم الحي",
    "مساحة": "المساحة (كم²)",
    "عدد_س": "عدد السكان (ألف نسمة)",
    "حدائق": "الحدائق",
    "إجمال": "إجمالي المساحات الخضراء (ألف م²)",
    "نصيب": "نصيب الفرد من المساحات الخضراء (م²/فرد)",
    "نسبة": "النسبة (%)",
}
POPUP_COLS = [k for k in COLUMN_LABELS if k != NAME_COL]
GREEN_SCALE = [[0.0, "#E5F5E0"], [0.25, "#A1D99B"], [0.5, "#41AB5D"], [0.75, "#238B45"], [1.0, "#00441B"]]


def to_number(v):
    if v is None:
        return np.nan
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("%", "").replace(",", "").strip())
    except ValueError:
        return np.nan


@st.cache_data(show_spinner=False)
def load():
    gdf = c.read_geo(c.data_path(APP, FILE))
    gdf[NAME_COL] = gdf[NAME_COL].apply(lambda v: re.sub(r"[_\[\]]+", " ", str(v)).strip())
    for col in POPUP_COLS:
        gdf[col] = gdf[col].apply(to_number)
    gdf["id"] = gdf.index.astype(str)
    return gdf


def fmt(value, col):
    if pd.isna(value):
        return "—"
    if col == "نسبة":
        return f"{value:.1f}%"
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


@st.cache_resource(show_spinner=False)
def build_map():
    gdf = load()
    geo = c.to_geojson(gdf, ["id"])
    hover = "<b>%{text}</b><br>"
    for i, col in enumerate(POPUP_COLS):
        hover += (f"<b>{COLUMN_LABELS[col]}: %{{customdata[{i}]:.2f}}</b><br>" if col == VALUE_COL
                  else f"{COLUMN_LABELS[col]}: %{{customdata[{i}]:,}}<br>")
    hover += "<i>انقر لعرض التفاصيل</i><extra></extra>"
    outline = go.Choroplethmap(   # solid white outlines under a semi-transparent fill
        geojson=geo, featureidkey="properties.id", locations=gdf["id"], z=[0] * len(gdf),
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
        marker_line_width=1.5, marker_line_color="white", hoverinfo="skip")
    fill = go.Choroplethmap(
        geojson=geo, featureidkey="properties.id", locations=gdf["id"], z=gdf[VALUE_COL],
        colorscale=GREEN_SCALE, marker_opacity=c.FILL_OPACITY, marker_line_width=0,
        selected=dict(marker=dict(opacity=1.0)), unselected=dict(marker=dict(opacity=c.FILL_OPACITY)),
        text=gdf[NAME_COL], customdata=gdf[POPUP_COLS].to_numpy(), hovertemplate=hover,
        colorbar=c.plotly_colorbar("<b>نصيب الفرد<br>(م²/فرد)</b>", tickformat=".1f"))
    return c.plotly_map_layout(go.Figure([outline, fill]), gdf.total_bounds)


@st.dialog("تفاصيل الحي", width="large")
def show_popup(row):
    st.markdown(f"<h3 style='color:{c.NAVY};margin-top:0'>{row[NAME_COL]}</h3>", unsafe_allow_html=True)
    rows = "".join(
        f'<tr{" class=highlight-row" if col == VALUE_COL else ""}><td>{COLUMN_LABELS[col]}</td>'
        f'<td>{fmt(row[col], col)}</td></tr>' for col in POPUP_COLS)
    st.markdown(f'<table class="info-table">{rows}</table>', unsafe_allow_html=True)


# ---------------------------------------------------------------- page
c.require_files(APP, [FILE])
gdf = load()
c.page_title(TITLE, "🌳")

k = st.columns(4)
best, worst = gdf.loc[gdf[VALUE_COL].idxmax()], gdf.loc[gdf[VALUE_COL].idxmin()]
total_pop = gdf["عدد_س"].sum()
k[0].metric("عدد الأحياء", f"{len(gdf)}")
k[1].metric("المتوسط العام (م²/فرد)", f"{gdf['إجمال'].sum() / total_pop:.2f}" if total_pop else "—")
k[2].metric("الأعلى (م²/فرد)", f"{best[VALUE_COL]:.2f}", best[NAME_COL], delta_color="off")
k[3].metric("الأدنى (م²/فرد)", f"{worst[VALUE_COL]:.2f}", worst[NAME_COL], delta_color="off")
c.metric_cards()

event = st.plotly_chart(build_map(), key="green_map", on_select="rerun", selection_mode="points",
                        config={"scrollZoom": True, "displaylogo": False}, use_container_width=True)
clicked = None
if event and event.selection and event.selection.points:
    for p in event.selection.points:
        if p.get("curve_number", 1) == 1:
            loc = p.get("location")
            if loc is None and p.get("point_index") is not None:
                loc = gdf["id"].iloc[p["point_index"]]
            clicked = str(loc)
            break
if clicked is not None and clicked != st.session_state.get("green_last"):
    st.session_state["green_last"] = clicked
    show_popup(gdf[gdf["id"] == clicked].iloc[0])
if clicked is None:
    st.session_state["green_last"] = None
st.caption("انقر على أي حي في الخريطة لعرض كل بياناته.")

with st.expander("ترتيب الأحياء حسب نصيب الفرد"):
    ranked = gdf.sort_values(VALUE_COL)
    fig = go.Figure(go.Bar(
        x=ranked[VALUE_COL], y=ranked[NAME_COL] + "  ", orientation="h",
        marker_color=[c.BLUE if i == clicked else "#238B45" for i in ranked["id"]],
        text=ranked[VALUE_COL].map(lambda v: f"{v:.2f}"), textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.2f} م²/فرد<extra></extra>"))
    c.bar_layout(fig, 380, xaxis_title="م²/فرد", yaxis=dict(side="right"))
    c.show_chart(fig)

with st.expander("جدول البيانات الكامل"):
    table = gdf[[NAME_COL] + POPUP_COLS].rename(columns=COLUMN_LABELS)
    st.dataframe(table.sort_values(COLUMN_LABELS[VALUE_COL], ascending=False), hide_index=True,
                 use_container_width=True)
