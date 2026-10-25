# -*- coding: utf-8 -*-
"""استخدامات كورنيش رأس البر 2024 — data in data/rasbar/, photos in static/photos/rasbar/"""
import corniche

USE = ["نوع الاستخدام", "عدد طوابق المنشأة", "مادة البناء", "طول الاستخدام (م)",
       "مساحة الاستخدام (م2)", "الوحدة الإدارية"]
BEACH = ["وصف الشاطئ", "الطول (م)", "المساحة (م2)"]

corniche.run(dict(
    app="rasbar", title="استخدامات كورنيش رأس البر 2024", icon="🏖️", utm=32636,
    use_name_col="اسم الاستخدام", area_col="مساحة الاستخدام (م2)", photos=True, cards="share",
    layers=[  # legend order, top to bottom
        dict(key="blocking", name="حجب رؤية البحر عن الممشى", file="RasElBar_sea_view_blocking.geojson",
             fill="#D22A14", border="#D22A14", kind="line"),
        dict(key="work", name="منطقة عمل", file="RasElBar_work_area.geojson",
             fill="#9A9A9A", border="#9A9A9A", kind="use", name_col="اسم الاستخدام", fields=USE),
        dict(key="unidentified", name="لم يُستدل", file="RasElBar_unidentified.geojson",
             fill="#F9FFB2", border="#F9FFB2", kind="use", name_col="اسم الاستخدام", fields=USE),
        dict(key="cafes", name="كافيهات", file="RasElBar_cafes.geojson",
             fill="#CDA23F", border="#CDA23F", kind="use", name_col="اسم الاستخدام", fields=USE),
        dict(key="private", name="شاطئ خاص", file="RasElBar_private_beaches.geojson",
             fill="#294376", border="#5B7FC4", kind="use", name_col="اسم الاستخدام", fields=USE),
        dict(key="beach", name="شاطئ كورنيش رأس البر", file="RasElBar_corniche_beach.geojson",
             fill="#A9D0E7", border="#A9D0E7", kind="beach", name_col="اسم الشاطئ", fields=BEACH,
             length_col="الطول (م)"),
        dict(key="governorate", name="محافظة دمياط", file="RasElBar_damietta_governorate.geojson",
             fill="#E5DEC4", border="#E5DEC4", kind="context"),
    ],
))
