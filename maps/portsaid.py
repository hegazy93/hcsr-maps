# -*- coding: utf-8 -*-
"""استخدامات كورنيش بورسعيد 2024 — data in data/portsaid/, photos in static/photos/portsaid/"""
import corniche

USE = ["نوع الاستخدام", "عدد طوابق المنشأة", "مادة البناء", "طول الاستخدام (م)",
       "مساحة الاستخدام (م2)", "الوحدة الإدارية (حي)"]
BEACH = ["وصف الشاطئ", "طول الشاطئ (م)", "مساحة الشاطئ (م2)"]


def use(key, name, file, fill, border=None):
    return dict(key=key, name=name, file=file, fill=fill, border=border or fill, kind="use",
                name_col="اسم الاستخدام", fields=USE)


corniche.run(dict(
    app="portsaid", title="استخدامات كورنيش بورسعيد 2024", icon="🏖️", utm=32636,
    use_name_col="اسم الاستخدام", area_col="مساحة الاستخدام (م2)", photos=True, cards="share",
    district_col="الوحدة الإدارية (حي)",
    layers=[  # legend order, top to bottom
        dict(key="blocking", name="حجب رؤية البحر عن الممشى", file="PortSaid_sea_view_blocking.geojson",
             fill="#D22A14", border="#D22A14", kind="line"),
        use("services", "خدمات شاطئ", "PortSaid_beach_services.geojson", "#4FE5E9"),
        use("private", "شاطئ خاص", "PortSaid_private_beaches.geojson", "#294376", "#5B7FC4"),
        use("halls", "قاعات حفلات ومناسبات", "PortSaid_event_halls.geojson", "#D4FFBE"),
        use("cafes", "كافيهات", "PortSaid_cafes.geojson", "#CDA23F"),
        use("unidentified", "لم يُستدل", "PortSaid_unidentified.geojson", "#F9FFB2"),
        use("sports", "منشآت رياضية", "PortSaid_sports.geojson", "#488537", "#6FB55A"),
        use("work", "منطقة عمل", "PortSaid_work_area.geojson", "#9A9A9A"),
        dict(key="beach_rented", name="شاطئ مجاني مُستأجر", file="PortSaid_free_rented_beach.geojson",
             fill="#A9D0E7", border="#A9D0E7", kind="beach", name_col="اسم الشاطئ", fields=BEACH,
             length_col="طول الشاطئ (م)"),
        dict(key="beach_open", name="شاطئ مجاني مفتوح", file="PortSaid_free_open_beach.geojson",
             fill="#B9E5FF", border="#B9E5FF", kind="beach", name_col="اسم الشاطئ", fields=BEACH,
             length_col="طول الشاطئ (م)"),
        dict(key="governorate", name="محافظة بورسعيد", file="PortSaid_governorate.geojson",
             fill="#E5DEC4", border="#E5DEC4", kind="context"),
    ],
))
