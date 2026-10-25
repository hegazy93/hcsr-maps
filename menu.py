# -*- coding: utf-8 -*-
"""The list of maps shown in the dropdown and on the home page.
To add a map: put its page in maps/, its data in data/<name>/, and add one line here."""

# (page file, title in the dropdown, icon, web address, one-line description)
MAPS = [
    ("maps/greenspace.py", "نصيب الفرد من المساحات الخضراء", "🌳", "greenspace",
     "نصيب الفرد من المساحات الخضراء في أحياء محافظة الإسكندرية."),
    ("maps/heat.py", "الجزر الحرارية بالإسكندرية", "🌡️", "heat-islands",
     "أنماط الجزر الحرارية ومتوسط درجات الحرارة الفصلية (2000-2020)."),
    ("maps/roads.py", "المحاور والطرق والكباري", "🛣️", "roads",
     "محاور الإسكندرية الجديدة وطرقها وكباريها (2014-2024)."),
    ("maps/transport.py", "خطوط المواصلات العامة", "🚌", "transport",
     "خطوط الأتوبيسات والميكروباصات والترام والقطار والمواقف الرئيسية (2023)."),
    ("maps/collapses.py", "العقارات المنهارة", "🏚️", "collapsed-buildings",
     "حصر العقارات المنهارة وضحاياها (يناير 2021 - يوليو 2023)."),
    ("maps/alex_waterfront.py", "كورنيش الإسكندرية", "🌊", "alexandria-corniche",
     "استخدامات كورنيش الإسكندرية وحجب رؤية البحر عن الممشى."),
    ("maps/baltim.py", "كورنيش بلطيم", "🏝️", "baltim",
     "استخدامات كورنيش بلطيم وحجب رؤية البحر."),
    ("maps/rasbar.py", "كورنيش رأس البر", "🏖️", "ras-el-bar",
     "استخدامات كورنيش رأس البر وحجب رؤية البحر."),
    ("maps/portsaid.py", "كورنيش بورسعيد", "⚓", "port-said",
     "استخدامات كورنيش بورسعيد وشواطئه وحجب رؤية البحر، حسب الحي."),
]
HOME = ("maps/home.py", "الرئيسية", "🏠")
SITE_TITLE = "خرائط HCSR التفاعلية"   # shown on the home page and browser tab
