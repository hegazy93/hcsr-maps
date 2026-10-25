# -*- coding: utf-8 -*-
"""استخدامات كورنيش الإسكندرية 2024 — data in data/alex_waterfront/,
photos in static/photos/alex_waterfront/.
Note for the client report: the "حجب الرؤية" lines are derived from each use's "رؤية البحر"
attribute (لا / لا بشكل مؤقت), drawn along its landward edge; the original legend classes
"شاطئ مجاني" and "شاطئ الخدمة لمن يطلبها" are not shown because the client's data has none."""
import corniche

USE = ["النوع", "الوصف", "إمكانية رؤية البحر", "الطول (م)", "المساحة (م2)", "المنطقة", "الحي"]


def use(key, name, file, fill, border=None):
    return dict(key=key, name=name, file=file, fill=fill, border=border or fill, kind="use",
                name_col="الاسم", fields=USE)


corniche.run(dict(
    app="alex_waterfront", title="استخدامات كورنيش الإسكندرية 2024", icon="🏖️", utm=32635,
    use_name_col="الاسم", area_col="المساحة (م2)", photos=True, cards="view",
    district_col="الحي", view_col="إمكانية رؤية البحر", two_block_classes=True,
    layers=[  # legend order, top to bottom
        dict(key="blocking", name="حجب الرؤية", file="Alex_sea_view_blocking.geojson",
             fill="#BC0013", border="#BC0013", kind="line"),
        use("public", "شاطئ عام", "Alex_public_beaches.geojson", "#83C8F8"),
        use("premium", "شاطئ مميز", "Alex_premium_beaches.geojson", "#2671C1", "#4D8FD6"),
        use("tourist", "شاطئ سياحي", "Alex_tourist_beaches.geojson", "#2658A9", "#4D7CC6"),
        use("private", "شاطئ خاص", "Alex_private_beaches.geojson", "#29457F", "#5B7FC4"),
        use("work", "منطقة عمل", "Alex_work_area.geojson", "#9A9A9A"),
        use("cafes", "كافيتريات", "Alex_cafeterias.geojson", "#CDA23F"),
        use("clubs", "نوادي", "Alex_clubs.geojson", "#488537", "#6FB55A"),
        use("hotels", "فنادق", "Alex_hotels.geojson", "#D4FFBE"),
        use("garages", "جراجات", "Alex_garages.geojson", "#F47040"),
        use("harbours", "مرفأ", "Alex_harbours.geojson", "#F8CA41"),
        use("other", "أخرى", "Alex_other.geojson", "#F9FFB2"),
        dict(key="governorate", name="محافظة الإسكندرية", file="Alex_governorate.geojson",
             fill="#F1EACD", border="#F1EACD", kind="context"),
    ],
))
