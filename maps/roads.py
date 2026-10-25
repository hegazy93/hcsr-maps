# -*- coding: utf-8 -*-
"""محاور الإسكندرية الجديدة وطرقها فى الفترة (2014-2024) — data in data/roads/"""
import folium
import pandas as pd
import streamlit as st

import common as c

APP = "roads"
TITLE = "محاور الإسكندرية الجديدة وطرقها فى الفترة (2014-2024)"
NAME_COL = "اسم المشروع"
POPUP_COLS = ["نوع المشروع", "الجهة", "تاريخ التنفيذ", "التكلفة",
              "حالة التنفيذ حتى (نوفمبر2023)", "وصف المشروع"]
ICON_FILE = "561.svg"
ICON_SIZE = (22, 31)
# legend order, top to bottom: (key, name, file, fill, border, kind)
LAYERS = [
    ("bridges", "الكبارى", "Alexandria_bridges.geojson", "#287014", "#287014", "polygon"),
    ("axes", "المحاور", "Alexandria_axes.geojson", "#EF1920", "#EF1920", "polygon"),
    ("roads", "الطرق", "Alexandria_roads.geojson", "#E17116", "#E17116", "polygon"),
    ("road_services", "خدمة طريق", "Alexandria_road_services.geojson", "#00A389", "#FFFFFF", "point"),
]


@st.cache_data(show_spinner=False)
def load():
    out = {}
    for key, name, file, fill, _b, _k in LAYERS:
        gdf = c.read_geo(c.data_path(APP, file))
        for col in [NAME_COL] + POPUP_COLS:
            if col not in gdf.columns:
                gdf[col] = ""
            gdf[col] = gdf[col].fillna("—").astype(str).str.strip()
        gdf["popup"] = [c.popup_html(r[NAME_COL], name, fill, [(f, r[f]) for f in POPUP_COLS],
                                     badge_text=c.text_on(fill)) for _, r in gdf.iterrows()]
        gdf["tip"] = [c.tip_html(r[NAME_COL], name) for _, r in gdf.iterrows()]
        out[key] = gdf
    return out


@st.cache_resource(max_entries=c.MAP_CACHE_ENTRIES, show_spinner=False)
def build_map():
    data = load()
    m = c.new_map()
    uri = c.file_data_uri(c.data_path(APP, ICON_FILE))
    for key, name, _f, fill, border, kind in reversed(LAYERS):   # bottom layer first
        gdf = data[key]
        if kind == "point":
            fg = c.group(m, c.lg_label(name, c.lg_img(uri) or c.lg_dot(fill), len(gdf)))
            w, h = ICON_SIZE
            for _, r in gdf.iterrows():
                icon = (folium.DivIcon(html=f'<img src="{uri}" style="width:{w}px;height:{h}px;'
                                            f'filter:drop-shadow(0 0 2px rgba(0,0,0,0.8))">',
                                       icon_size=(w, h), icon_anchor=(w // 2, h // 2))
                        if uri else folium.Icon(color="green"))
                folium.Marker([r.geometry.y, r.geometry.x], icon=icon, tooltip=folium.Tooltip(r["tip"]),
                              popup=folium.Popup(r["popup"], max_width=460)).add_to(fg)
            continue
        fg = c.group(m, c.lg_label(name, c.lg_swatch(c.hex_to_rgba(fill, 0.8), border), len(gdf)))
        c.add_geojson(fg, c.to_geojson(gdf, ["popup", "tip"]),
                      lambda _f, fill=fill, border=border: {
                          "fillColor": fill, "fillOpacity": c.FILL_OPACITY, "color": border,
                          "weight": 2, "opacity": 1})
    b = pd.DataFrame([g.total_bounds for g in data.values()])
    return c.finish_map(m, (b[0].min(), b[1].min(), b[2].max(), b[3].max()), padding=10)


# ---------------------------------------------------------------- page
c.require_files(APP, [l[2] for l in LAYERS])
data = load()
c.page_title(TITLE, "🛣️")

k = st.columns(5)
k[0].metric("إجمالي المشروعات", sum(len(g) for g in data.values()))
for col, (key, name, *_r) in zip(k[1:], LAYERS):
    col.metric(name, len(data[key]))
c.metric_cards()

c.show_map(build_map(), key="roads_map")
st.caption("انقر على أي مشروع في الخريطة لعرض تفاصيله. استخدم مفتاح الخريطة لإظهار الطبقات أو إخفائها.")

with st.expander("جدول المشروعات الكامل"):
    table = pd.concat([pd.DataFrame(data[key][[NAME_COL] + POPUP_COLS]).assign(الطبقة=name)
                       for key, name, *_r in LAYERS])
    st.dataframe(table[["الطبقة", NAME_COL] + POPUP_COLS], hide_index=True, use_container_width=True)
