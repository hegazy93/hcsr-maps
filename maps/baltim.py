# -*- coding: utf-8 -*-
"""استخدامات كورنيش بلطيم 2024 — data in data/baltim/, photos in static/photos/baltim/"""
import corniche

USE = ["نوع الاستخدام", "عدد طوابق المنشأة", "مادة البناء", "طول الاستخدام (م)",
       "مساحة الاستخدام (م2)", "الوحدة الإدارية"]
BEACH = ["وصف الشاطئ", "الطول (م)", "المساحة (م2)"]

corniche.run(dict(
    app="baltim", title="استخدامات كورنيش بلطيم 2024", icon="🏖️", utm=32636,
    use_name_col="اسم الاستخدام", area_col="مساحة الاستخدام (م2)", photos=True, cards="share",
    layers=[  # legend order, top to bottom
        dict(key="blocking", name="حجب رؤية البحر عن الممشى", file="Baltim_sea_view_blocking.geojson",
             fill="#E31A1C", border="#E31A1C", kind="line"),
        dict(key="beach", name="شاطئ مجاني مُستأجر", file="Baltim_corniche_beach.geojson",
             fill="#9AC8E3", border="#9AC8E3", kind="beach", name_col="اسم الشاطئ", fields=BEACH,
             length_col="الطول (م)"),
        dict(key="sports", name="منشآت رياضية", file="Baltim_sports.geojson",
             fill="#287014", border="#4E9A36", kind="use", name_col="اسم الاستخدام", fields=USE),
        dict(key="shops", name="محلات تجارية", file="Baltim_shops.geojson",
             fill="#F2571E", border="#F2571E", kind="use", name_col="اسم الاستخدام", fields=USE),
        dict(key="cafes", name="كافيهات", file="Baltim_cafes.geojson",
             fill="#C4921D", border="#C4921D", kind="use", name_col="اسم الاستخدام", fields=USE),
        dict(key="governorate", name="محافظة كفر الشيخ", file="Baltim_kafr_elsheikh_governorate.geojson",
             fill="#E0D8BA", border="#E0D8BA", kind="context"),
    ],
))
