# -*- coding: utf-8 -*-
"""
One engine for all corniche land-use maps (Ras El Bar, Port Said, Alexandria, Baltim).
Each page only describes its layers in a small settings dictionary and calls run(cfg).
"""

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import common as c

LINE_LEN = "الطول (م)"
BLOCK_COLOR, BLOCK_TEMP_COLOR = "#BC0013", "#4E4E4E"
VIEW_CLASSES = [("نعم", "متاحة", "#2E9E5B"), ("لا", "محجوبة", "#BC0013"),
                ("لا بشكل مؤقت", "محجوبة مؤقتاً", "#4E4E4E")]
CAUSE_FIELDS = ["الاستخدام المسبب للحجب", "نوع الاستخدام", "المنطقة"]

_REGISTRY = {}


def _clean_view(v):
    if not isinstance(v, str):
        return None
    v = " ".join(v.split())
    return "لا بشكل مؤقت" if "مؤقت" in v else v


def _view_label(v):
    return {k: lab for k, lab, _ in VIEW_CLASSES}.get(v, "—")


# ---------------------------------------------------------------- data (cached once per map)
@st.cache_data(show_spinner=False)
def _load(app):
    cfg = _REGISTRY[app]
    district, view = cfg.get("district_col"), cfg.get("view_col")
    out = {}
    for L in cfg["layers"]:
        kind = L["kind"]
        gdf = c.read_geo(c.data_path(app, L["file"]),
                         simplify=0.0003 if kind == "context" else None)
        if kind == "context":
            out[L["key"]] = gdf
            continue
        if kind == "line":
            gdf[LINE_LEN] = gdf.to_crs(epsg=cfg["utm"]).length.round(1)
            text = gdf.drop(columns="geometry").astype(str).agg(" ".join, axis=1)
            gdf["temporary"] = text.str.contains("مؤقت")
            fields = [f for f in CAUSE_FIELDS + ([district] if district else []) + [LINE_LEN]
                      if f in gdf.columns]
            pops, tips = [], []
            for i, r in gdf.iterrows():
                label = "حجب رؤية مؤقت" if r["temporary"] else (
                    "حجب رؤية" if cfg.get("two_block_classes") else L["name"])
                color = BLOCK_TEMP_COLOR if r["temporary"] else L["fill"]
                pops.append(c.popup_html(f"{label} — مقطع {i + 1}", label, color,
                                         [(f, c.fmt(r.get(f))) for f in fields]))
                tips.append(c.tip_html(label, f"الطول: {c.fmt(r[LINE_LEN])} م"))
            gdf["popup"], gdf["tip"] = pops, tips
            out[L["key"]] = gdf
            continue

        # polygons (uses and beaches)
        for col in L["fields"] + [L["name_col"]]:
            if col not in gdf.columns:
                gdf[col] = None
        if view and view in gdf.columns:
            gdf[view] = gdf[view].apply(_clean_view)
        pops, tips = [], []
        for _, r in gdf.iterrows():
            rows = []
            for f in L["fields"]:
                val = c.fmt(r.get(f))
                if f == view and isinstance(r.get(f), str):
                    vc = {k: col for k, _l, col in VIEW_CLASSES}.get(r[f], c.TEXT_DARK)
                    val = f'<b style="color:{vc}">{r[f]} ({_view_label(r[f])})</b>'
                rows.append((f, val))
            title = r[L["name_col"]] or L["name"]
            photo = c.photo_url(app, r.get(cfg.get("photo_col", "الصورة")))
            pops.append(c.popup_html(title, L["name"], L["fill"], rows, photo, c.text_on(L["fill"])))
            sub = L["name"] + (f" — رؤية البحر: {_view_label(r.get(view))}" if view else "")
            tips.append(c.tip_html(title, sub))
        gdf["popup"], gdf["tip"] = pops, tips
        out[L["key"]] = gdf
    return out


def _filtered(app, districts):
    cfg = _REGISTRY[app]
    data = _load(app)
    col = cfg.get("district_col")
    if not districts or not col:
        return data
    return {k: (g[g[col].isin(districts)] if col in g.columns and k != "governorate" else g)
            for k, g in data.items()}


# ---------------------------------------------------------------- map (cached per filter)
@st.cache_resource(max_entries=c.MAP_CACHE_ENTRIES, show_spinner=False)
def _map(app, districts):
    cfg = _REGISTRY[app]
    data = _filtered(app, districts)
    m = c.new_map()
    for L in reversed(cfg["layers"]):            # bottom layer first
        gdf, kind, fill, border = data[L["key"]], L["kind"], L["fill"], L["border"]
        if kind == "context":
            fg = c.group(m, c.lg_label(L["name"], c.lg_swatch(fill, border)))
            if len(gdf):
                folium.GeoJson(c.to_geojson(gdf, []),
                               style_function=lambda _f, fill=fill: {
                                   "fillColor": fill, "fillOpacity": 0.35, "color": fill,
                                   "weight": 1, "opacity": 0.6}).add_to(fg)
            continue
        if kind == "line":
            parts = [(True, BLOCK_TEMP_COLOR, "حجب رؤية مؤقت"),
                     (False, fill, "حجب رؤية" if cfg.get("two_block_classes") else L["name"])]
            for temp, color, label in parts:
                sub = gdf[gdf["temporary"] == temp]
                if temp and not cfg.get("two_block_classes") and sub.empty:
                    continue
                fg = c.group(m, c.lg_label(label, c.lg_line(color), len(sub)))
                c.add_geojson(fg, c.to_geojson(sub, ["popup", "tip"]),
                              lambda _f, col=color: {"color": col, "weight": 4, "opacity": 1},
                              weight_hover=6)
            continue
        fg = c.group(m, c.lg_label(L["name"], c.lg_swatch(fill, border), len(gdf)))
        c.add_geojson(fg, c.to_geojson(gdf, ["popup", "tip"]),
                      lambda _f, fill=fill, border=border: {
                          "fillColor": fill, "fillOpacity": c.FILL_OPACITY, "color": border,
                          "weight": 2, "opacity": 1})

    full = _load(app)
    b = pd.DataFrame([full[L["key"]].total_bounds for L in cfg["layers"]
                      if L["kind"] != "context" and len(full[L["key"]])])
    bounds = (b[0].min(), b[1].min(), b[2].max(), b[3].max())
    return c.finish_map(m, bounds)


# ---------------------------------------------------------------- page
def run(cfg):
    app = cfg["app"]
    _REGISTRY[app] = cfg
    c.require_files(app, [L["file"] for L in cfg["layers"]])
    data_all = _load(app)

    districts = ()
    dcol = cfg.get("district_col")
    if dcol:
        opts = sorted({d for L in cfg["layers"] if L["kind"] == "use"
                       for d in data_all[L["key"]][dcol].dropna().unique()})
        with st.sidebar:
            st.header("إعدادات الخريطة")
            chosen = st.multiselect("الأحياء", opts, default=opts, key=f"{app}_districts")
        districts = () if set(chosen) == set(opts) else tuple(sorted(chosen))
    data = _filtered(app, districts)

    c.page_title(cfg["title"], cfg.get("icon", "🏖️"))

    use_layers = [L for L in cfg["layers"] if L["kind"] == "use"]
    beach_layers = [L for L in cfg["layers"] if L["kind"] == "beach"]
    line_layers = [L for L in cfg["layers"] if L["kind"] == "line"]
    name_col, area_col = cfg["use_name_col"], cfg["area_col"]
    uses = pd.concat([pd.DataFrame(data[L["key"]].drop(columns=["geometry", "popup", "tip"]))
                     .assign(الطبقة=L["name"]) for L in use_layers], ignore_index=True)
    bl = pd.concat([data[L["key"]] for L in line_layers]) if line_layers else pd.DataFrame()
    block_len = float(bl[LINE_LEN].sum()) if len(bl) else 0.0
    tmp_len = float(bl.loc[bl["temporary"], LINE_LEN].sum()) if len(bl) else 0.0

    # metric cards
    k = st.columns(5)
    k[0].metric("عدد المنشآت على الكورنيش", f"{len(uses)}")
    k[1].metric("المساحة المشغولة (م²)", f"{pd.to_numeric(uses[area_col], errors='coerce').sum():,.0f}")
    if cfg.get("cards") == "view":
        view = cfg["view_col"]
        n = len(uses)
        nb, nt = int((uses[view] == "لا").sum()), int((uses[view] == "لا بشكل مؤقت").sum())
        k[2].metric("طول حجب رؤية البحر (كم)", f"{block_len / 1000:,.1f}",
                    f"منها {tmp_len / 1000:,.1f} كم حجب مؤقت", delta_color="off")
        k[3].metric("استخدامات تحجب رؤية البحر", f"{nb}",
                    f"{100 * nb / n:.0f}% من الاستخدامات" if n else None, delta_color="off")
        k[4].metric("تحجب الرؤية بشكل مؤقت", f"{nt}",
                    f"{100 * nt / n:.0f}% من الاستخدامات" if n else None, delta_color="off")
    else:
        beach_len = float(sum(pd.to_numeric(data[L["key"]][L["length_col"]], errors="coerce").sum()
                              for L in beach_layers))
        k[2].metric("طول شاطئ الكورنيش (م)", f"{beach_len:,.0f}")
        k[3].metric("طول حجب رؤية البحر (م)", f"{block_len:,.0f}")
        k[4].metric("نسبة الحجب من طول الكورنيش",
                    f"{100 * block_len / beach_len:.0f}%" if beach_len else "—")
    c.metric_cards()

    # map (built once per filter combination, then served from memory)
    c.show_map(_map(app, districts), key=f"{app}_map")
    note = "انقر على أي منشأة في الخريطة لعرض تفاصيلها. استخدم مفتاح الخريطة لإظهار الطبقات أو إخفائها."
    if cfg.get("photos") and not c.photos_available(app):
        note += f" ⚠️ لم يتم العثور على الصور في مجلد static/photos/{app}."
    st.caption(note)

    # charts
    names = [L["name"] for L in use_layers]
    colors = {L["name"]: L["fill"] for L in use_layers}
    uses[area_col] = pd.to_numeric(uses[area_col], errors="coerce")

    with st.expander("المنشآت حسب نوع الاستخدام"):
        summ = (uses.groupby("الطبقة").agg(العدد=(name_col, "size"), المساحة=(area_col, "sum"))
                .reindex(names).dropna())
        cols = st.columns(2)
        for col, metric, title in [(cols[0], "العدد", "عدد المنشآت"), (cols[1], "المساحة", "المساحة (م²)")]:
            fig = go.Figure(go.Bar(
                x=summ.index, y=summ[metric], marker_color=[colors[n] for n in summ.index],
                marker_line_color=c.NAVY, marker_line_width=0.6,
                text=summ[metric].map(lambda v: f"{v:,.0f}"), textposition="outside",
                hovertemplate="<b>%{x}</b><br>" + title + ": %{y:,.0f}<extra></extra>"))
            c.bar_layout(fig, 360, title=dict(text=title, x=0.5), xaxis=dict(autorange="reversed"))
            fig.update_layout(margin={"r": 10, "t": 40, "l": 10, "b": 60})
            with col:
                c.show_chart(fig)

    if cfg.get("view_col"):
        view = cfg["view_col"]
        with st.expander("إمكانية رؤية البحر حسب نوع الاستخدام"):
            vv = uses.groupby(["الطبقة", view]).size().unstack(fill_value=0).reindex(names).dropna(how="all")
            fig = go.Figure()
            for key, label, color in VIEW_CLASSES:
                if key in vv.columns:
                    fig.add_trace(go.Bar(name=f"الرؤية {label}", x=vv.index, y=vv[key], marker_color=color,
                                         hovertemplate="<b>%{x}</b><br>" + label + ": %{y}<extra></extra>"))
            c.bar_layout(fig, 380, barmode="stack", yaxis_title="عدد الاستخدامات",
                         xaxis=dict(autorange="reversed"),
                         legend=dict(orientation="h", y=1.12, x=1, xanchor="right"))
            c.show_chart(fig)

    if dcol:
        with st.expander("المنشآت حسب الحي"):
            bd = uses.groupby([dcol, "الطبقة"]).size().unstack(fill_value=0)
            order = bd.sum(axis=1).sort_values(ascending=False).index
            fig = go.Figure()
            for n in names:
                if n in bd.columns:
                    fig.add_trace(go.Bar(name=n, x=list(order), y=bd.loc[order, n], marker_color=colors[n],
                                         marker_line_color=c.NAVY, marker_line_width=0.4,
                                         hovertemplate="<b>%{x}</b><br>" + n + ": %{y}<extra></extra>"))
            c.bar_layout(fig, 400, barmode="stack", yaxis_title="عدد المنشآت",
                         xaxis=dict(autorange="reversed"),
                         legend=dict(orientation="h", y=1.18, x=1, xanchor="right"))
            c.show_chart(fig)

    top_n = cfg.get("top_n", 20)
    with st.expander(f"أكبر {top_n} منشأة حسب المساحة" if len(uses) > top_n else "المنشآت مرتبة حسب المساحة"):
        top = uses.dropna(subset=[area_col]).sort_values(area_col).tail(top_n)
        labels = c.unique_labels([str(x) for x in top[name_col].fillna("—")])
        fig = go.Figure(go.Bar(
            x=top[area_col], y=[l + "  " for l in labels], orientation="h",
            marker_color=[colors[n] for n in top["الطبقة"]], marker_line_color=c.NAVY,
            marker_line_width=0.4, customdata=top["الطبقة"],
            text=top[area_col].map(lambda v: f"{v:,.0f}"), textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{customdata}<br>%{x:,.0f} م²<extra></extra>"))
        c.bar_layout(fig, max(380, 24 * len(top)), xaxis_title="المساحة (م²)", yaxis=dict(side="right"))
        c.show_chart(fig)

    with st.expander("جدول المنشآت الكامل"):
        fields = [f for f in use_layers[0]["fields"] if f in uses.columns]
        st.dataframe(uses[["الطبقة", name_col] + fields], hide_index=True, use_container_width=True)
