"""Builds Factorio-style UI mockups (HTML) from real tooltip fields recorded in the headless server.

These are mockups, not game screenshots: the headless server has no graphics. The text inside the
tooltips is exactly what the mod wrote into the entities, localised with the mod's locale files.
"""
import html
import json
import os
import re
import sys

DEV = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(DEV)
FONT = DEV + "/node_modules/@fontsource/titillium-web/files/titillium-web-latin-%s-normal.woff2"


def load_locale(path):
    entries, section = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        header = re.match(r"\[(.+)\]$", line)
        if header:
            section = header.group(1)
        elif "=" in line and section:
            key, value = line.split("=", 1)
            entries[section + "." + key] = value
    return entries


def localise(value, locale):
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return "%g" % value
    key, params = value[0], [localise(p, locale) for p in value[1:]]
    if key == "":
        return "".join(params)
    text = locale[key]
    for index, param in enumerate(params):
        text = text.replace("__%d__" % (index + 1), param)
    return text


def rich(text):
    text = html.escape(text)
    return re.sub(r"\[item=([a-z0-9-]+)\]", r'<span class="icon" title="\1">\1</span>', text)


LOCALES = {lang: load_locale(f"{MOD}/locale/{lang}/locale.cfg") for lang in ("en", "ru")}
QUALITY = {
    "normal": ("Normal", "Обычное", None),
    "uncommon": ("Uncommon", "Необычное", "#2ba53d"),
    "rare": ("Rare", "Редкое", "#1968b2"),
    "epic": ("Epic", "Эпическое", "#b04ee0"),
    "legendary": ("Legendary", "Легендарное", "#b26800"),
}
NAMES = {
    "inserter": ("Inserter", "Манипулятор"),
    "fast-inserter": ("Fast inserter", "Быстрый манипулятор"),
    "long-handed-inserter": ("Long-handed inserter", "Длинный манипулятор"),
    "bulk-inserter": ("Bulk inserter", "Массовый манипулятор"),
    "stack-inserter": ("Stack inserter", "Пакетный манипулятор"),
}
SCENARIOS = {
    "1": ("Chest → turbo belt, all research", "Сундук → турбо-конвейер, всё исследовано"),
    "2": ("Compressed turbo belt → chest (measured line enabled)", "Сжатый турбо-конвейер → сундук (включена строка «Измерено»)"),
    "3": ("Chest → chest, nothing researched yet", "Сундук → сундук, ничего не исследовано"),
    "4": ("Ghost (building plan) → express belt", "Призрак (план постройки) → экспресс-конвейер"),
    "5": ("Hand stack limited to 8 manually / by circuit", "Пачка ограничена до 8 вручную или сетью"),
    "6": ("Filtered to locomotives (stack size 5)", "Фильтр на локомотивы (стопка 5)"),
    "7": ("Belt → belt", "Конвейер → конвейер"),
}

STYLE = """
@font-face { font-family: 'Titillium Web'; font-weight: 400; src: url('file://%s'); }
@font-face { font-family: 'Titillium Web'; font-weight: 600; src: url('file://%s'); }
@font-face { font-family: 'Titillium Web'; font-weight: 700; src: url('file://%s'); }
* { box-sizing: border-box; }
body { margin: 0; padding: 28px; background: #16150f; font-family: 'Titillium Web', 'Noto Sans', sans-serif;
       color: #e8e6e3; width: 1180px; }
h1 { font-size: 22px; margin: 0 0 4px; color: #ffe6c0; font-weight: 700; }
.note { font-size: 14px; color: #a39f96; margin-bottom: 22px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 22px 26px; align-items: start; }
.card .caption { font-size: 14px; color: #c9c4b8; margin: 0 0 6px 2px; }
.tt { background: #242324; border: 1px solid #0b0b0b; box-shadow: 0 0 0 1px #3e3d3e inset, 0 6px 18px rgba(0,0,0,.6);
      border-radius: 3px; overflow: hidden; }
.tt-title { background: linear-gradient(#4a484a, #3a393a); padding: 7px 12px 6px; font-weight: 700; font-size: 18px;
            color: #ffe6c0; border-bottom: 1px solid #111; display: flex; gap: 10px; align-items: baseline; }
.tt-title .q { font-size: 15px; font-weight: 600; }
.tt-title .ghost { font-size: 14px; color: #9fc6ff; font-weight: 600; }
.tt-body { padding: 8px 12px 10px; font-size: 15px; line-height: 1.5; }
.vanilla { color: #8e8a83; font-size: 14px; }
.vanilla .ok { color: #5fd35f; }
.sep { height: 1px; background: #3b3a3b; margin: 6px -12px 6px; }
.row b { color: #ffe6c0; font-weight: 700; }
.row.main { font-size: 16px; }
.row.main .v { color: #ffffff; font-weight: 600; }
.icon { display: inline-block; font-size: 10px; line-height: 16px; padding: 0 4px; margin: 0 2px; border-radius: 2px;
        background: #3d3c3d; border: 1px solid #5a585a; color: #e0dccf; vertical-align: 1px; }
""" % (FONT % 400, FONT % 600, FONT % 700)


def tooltip_html(case_id, fields, lang):
    _, number, entity, quality = case_id.split("|")
    locale = LOCALES[lang]
    li = 0 if lang == "en" else 1
    q_en, q_ru, q_color = QUALITY[quality]
    quality_html = ""
    if q_color:
        quality_html = '<span class="q" style="color:%s">%s</span>' % (q_color, q_en if li == 0 else q_ru)
    ghost_html = ""
    status = ("Status:", "Working") if li == 0 else ("Состояние:", "Работает")
    if number == "4":
        ghost_html = '<span class="ghost">%s</span>' % ("Entity ghost" if li == 0 else "План объекта")
        vanilla = '<div class="vanilla">%s</div>' % ("…vanilla ghost tooltip lines…" if li == 0 else "…ванильные строки подсказки призрака…")
    else:
        vanilla = '<div class="vanilla">%s <span class="ok">● %s</span> &nbsp;…%s…</div>' % (
            status[0], status[1], "vanilla lines" if li == 0 else "ванильные строки")
    rows = []
    for index, field in enumerate(fields):
        name = rich(localise(field["name"], locale))
        value = rich(localise(field["value"], locale))
        cls = "row main" if index == 0 else "row"
        rows.append('<div class="%s"><b>%s:</b> <span class="v">%s</span></div>' % (cls, name, value))
    return """<div class="card"><div class="caption">%s</div><div class="tt">
<div class="tt-title">%s %s %s</div><div class="tt-body">%s<div class="sep"></div>%s</div></div></div>""" % (
        html.escape(SCENARIOS[number][li]), NAMES[entity][li], quality_html, ghost_html, vanilla, "\n".join(rows))


def tooltips_page(lang, cases, results):
    li = 0 if lang == "en" else 1
    title = ("Inserter Throughput Tooltip — tooltip mockup" if li == 0
             else "Пропускная способность манипуляторов — макет подсказки")
    note = ("Mockup, not a game screenshot (only a headless server was available). The lines below the separator are "
            "exactly what the mod wrote into real entities in Factorio 2.1.22, localised with the mod's locale. "
            "The part above the separator stands for the vanilla tooltip."
            if li == 0 else
            "Макет, а не скриншот игры (был доступен только headless-сервер). Строки под разделителем — ровно то, что "
            "мод записал в подсказки реальных сущностей в Factorio 2.1.22, переведённое файлами локали мода. "
            "Часть над разделителем условно обозначает ванильную подсказку.")
    cards = []
    for case_id, fields in cases:
        # The measured line is off by default; it is shown on one card only.
        fields = [f for f in fields if f["name"] != ["inserter-hover-throughput.measured"]]
        if case_id.split("|")[1] == "2":
            rate = results[case_id]["rate"]
            fields = fields + [{"name": ["inserter-hover-throughput.measured"],
                                "value": ["inserter-hover-throughput.measured-value", "%.1f" % rate, "10"]}]
        cards.append(tooltip_html(case_id, fields, lang))
    return "<!doctype html><html><head><meta charset='utf-8'><style>%s</style></head><body><h1>%s</h1><div class='note'>%s</div><div class='grid'>%s</div></body></html>" % (
        STYLE, html.escape(title), html.escape(note), "\n".join(cards))


SETTINGS_STYLE = STYLE + """
.windows { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }
.win { background: #313031; border: 1px solid #0b0b0b; box-shadow: 0 0 0 1px #4a494a inset, 0 6px 18px rgba(0,0,0,.6); border-radius: 3px; }
.win-title { padding: 8px 14px; font-weight: 700; font-size: 18px; color: #ffe6c0; }
.tabs { display: flex; gap: 4px; padding: 0 14px; }
.tab { padding: 5px 14px; background: #3d3c3d; color: #c9c4b8; border-radius: 3px 3px 0 0; font-size: 15px; font-weight: 600; }
.tab.on { background: #8e8a83; color: #1a1a1a; }
.inner { background: #242324; margin: 0 14px; padding: 12px 14px; box-shadow: 0 0 0 1px #0f0f0f inset; }
.group { font-weight: 700; color: #ffe6c0; font-size: 16px; margin-bottom: 8px; }
.opt { display: flex; gap: 10px; align-items: center; font-size: 15px; margin: 7px 0; }
.box { width: 18px; height: 18px; border-radius: 2px; background: #8e8a83; box-shadow: 0 0 0 1px #111 inset; flex: none;
       display: flex; align-items: center; justify-content: center; color: #1a1a1a; font-weight: 700; font-size: 14px; }
.box.on { background: #e0dccf; }
.desc { font-size: 13px; color: #a39f96; margin: -4px 0 6px 28px; }
.buttons { display: flex; justify-content: space-between; padding: 12px 14px; }
.btn { padding: 4px 18px; border-radius: 3px; font-weight: 700; font-size: 15px; color: #111; }
.btn.red { background: #e04d3c; } .btn.green { background: #5eb663; }
.world { margin-top: 26px; }
.scene { position: relative; height: 230px; border-radius: 3px; overflow: hidden; background-color: #4a4232;
         background-image: linear-gradient(rgba(0,0,0,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,.18) 1px, transparent 1px);
         background-size: 32px 32px; }
.belt { position: absolute; left: 0; right: 0; height: 32px; background: repeating-linear-gradient(90deg, #5a5a5a 0 6px, #444 6px 12px);
        box-shadow: 0 0 0 2px #2a2a2a inset; }
.chest { position: absolute; width: 30px; height: 30px; background: #6b5130; border: 2px solid #3a2a15; border-radius: 3px; }
.ins { position: absolute; width: 26px; height: 26px; background: #9d9d9d; border: 2px solid #3f3f3f; border-radius: 50%; }
.arm { position: absolute; width: 6px; background: #d0a030; border: 1px solid #5a4210; }
.label { position: absolute; transform: translateX(-50%); font-weight: 700; font-size: 17px; color: #fff; white-space: nowrap;
         text-shadow: 0 0 3px #000, 0 0 2px #000, 1px 1px 0 #000; }
.cursor { position: absolute; width: 34px; height: 34px; border: 2px solid #ffd060; border-radius: 3px; }
"""


def settings_page():
    def window(lang, tab, options):
        locale = LOCALES[lang]
        ru = lang == "ru"
        tabs = [("Startup", "Запуск"), ("Map", "Карта"), ("Per player", "Для каждого игрока")]
        tab_html = "".join('<div class="tab%s">%s</div>' % (" on" if i == tab else "", t[1] if ru else t[0])
                           for i, t in enumerate(tabs))
        opts = []
        for key, on in options:
            name = locale["mod-setting-name." + key]
            desc = locale["mod-setting-description." + key]
            opts.append('<div class="opt"><div class="box%s">%s</div>%s</div><div class="desc">%s</div>' % (
                " on" if on else "", "✓" if on else "", html.escape(name), html.escape(desc)))
        return """<div class="win"><div class="win-title">%s</div><div class="tabs">%s</div><div class="inner">
<div class="group">%s</div>%s</div><div class="buttons"><span class="btn red">%s</span><span class="btn green">%s</span></div></div>""" % (
            "Настройки модов" if ru else "Mod settings", tab_html, html.escape(locale["mod-name.inserter-hover-throughput"]),
            "".join(opts), "Отмена" if ru else "Cancel", "Применить" if ru else "Confirm")

    map_options = [("inserter-hover-throughput-prepare-ahead", True), ("inserter-hover-throughput-show-details", True),
                   ("inserter-hover-throughput-show-measured", False)]
    player_options = [("inserter-hover-throughput-show-label", False)]
    scene = """<div class="world"><div class="caption" style="font-size:14px;color:#c9c4b8;margin:0 0 6px 2px">%s</div><div class="scene">
<div class="belt" style="top:150px"></div>
<div class="chest" style="left:560px;top:52px"></div>
<div class="arm" style="left:572px;top:84px;height:34px"></div>
<div class="ins" style="left:562px;top:116px"></div>
<div class="cursor" style="left:558px;top:112px"></div>
<div class="label" style="left:577px;top:20px">⇄ 80/с (4800/мин)</div>
</div></div>""" % html.escape("Опция «Дублировать скорость надписью над манипулятором» (условная сцена, не скриншот): "
                              "надпись видна только этому игроку и исчезает, когда курсор уходит.")
    body = "<h1>%s</h1><div class='note'>%s</div><div class='windows'>%s%s%s%s</div>%s" % (
        "Настройки мода — макет", html.escape(
            "Макет окна «Настройки модов» (не скриншот игры). Тексты взяты из файлов локали мода; галочки — значения по умолчанию. "
            "«Карта» — общие для всей игры (в мультиплеере их меняет админ), «Для каждого игрока» — свои у каждого."),
        window("ru", 1, map_options), window("ru", 2, player_options),
        window("en", 1, map_options), window("en", 2, player_options), scene)
    return "<!doctype html><html><head><meta charset='utf-8'><style>%s</style></head><body>%s</body></html>" % (SETTINGS_STYLE, body)


if __name__ == "__main__":
    out_dir = sys.argv[1]
    cases = []
    for line in open(DEV + "/showcase_fields.txt", encoding="utf-8"):
        case_id, fields = line.split(" ", 1)
        cases.append((case_id, json.loads(fields)))
    results = {}
    for line in open(DEV + "/showcase_results.jsonl", encoding="utf-8"):
        result = json.loads(line)
        results[result["id"]] = result
    for lang in ("ru", "en"):
        open(f"{out_dir}/tooltip_{lang}.html", "w", encoding="utf-8").write(tooltips_page(lang, cases, results))
    open(f"{out_dir}/settings.html", "w", encoding="utf-8").write(settings_page())
