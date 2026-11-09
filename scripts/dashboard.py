#!/usr/bin/env python3
# English-coach istatistik sayfası: answers.csv + progress.md + curriculum.md → dashboard.html (internetsiz, tek dosya).
import csv
import html
import re
import sys
from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta
from pathlib import Path

DATA = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "English-Learning"
ANSWERS = DATA / "answers.csv"
PROGRESS = DATA / "progress.md"
OUT = DATA / "dashboard.html"
CURRICULUM = Path(__file__).resolve().parent.parent / "curriculum.md"

AREAS = ["Günlük konuşma", "Gramer", "Kelime ve kalıplar", "Yazılımcı İngilizcesi"]
GROUPS = ["Zaman", "Cümle", "Gramer", "Kelime"]
# Yazım hataları sadece not edilir: öğretmen notunda ve hata sıralamasında öne çıkmaz.
MINOR_TAG = "yazim"
RESULTS = [("ok", "✅ Doğru"), ("close", "🟡 Yakın"), ("wrong", "❌ Yanlış")]
POINTS = {"ok": 1.0, "close": 0.5, "wrong": 0.0}
DOTS = {"ok": "✅", "close": "🟡", "wrong": "❌"}
PRODUCTION = {"translate", "wordbox", "transform", "free"}
STATUSES = [
    ("good", "🟢 İyi"),
    ("developing", "🟠 Gelişiyor"),
    ("weak", "🔴 Zayıf"),
    ("review", "🔁 Tekrar zamanı"),
    ("learning", "🔵 Öğreniliyor"),
    ("new", "⚪ Başlanmadı"),
]
STATUS_LABEL = dict(STATUSES)
REVIEW_AFTER_DAYS = 14
# İş oturumundaki Better English düzeltmeleri: sadece hata istatistiğine girer, puana girmez.
WORK_KIND = "work-note"
# Oyun puanı: cevap sonucuna göre, sonuçsuz satırda kind'a göre.
XP_RESULT = {"ok": 10, "close": 5, "wrong": 2}
XP_KIND = {"lesson": 5, "tip": 2}
WEEKLY_GOAL = 40
CALENDAR_WEEKS = 12
TREND_WEEKS = 8
UNIT_NAMES = {"1": "Temel", "2": "Present simple", "3": "Şimdi ve yer", "4": "Geçmiş",
              "5": "Plan ve karşılaştırma", "6": "Bağlantılar", "K": "Kelime yolları"}
# Çalışma yönleri: soru tipine göre beceri.
SKILLS = [
    ("Türkçeden İngilizceye çeviri", {"translate"}),
    ("Kendi cümleni yazma", {"free", "wordbox"}),
    ("Hata düzeltme ve dönüştürme", {"correct", "transform"}),
    ("Tanıma (seçme, boşluk, sıralama)", {"choose", "gap", "order"}),
]
SKILL_WINDOW = 20


def read_answers():
    if not ANSWERS.exists():
        return []
    with ANSWERS.open(encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("date")]


def table_rows(text, heading):
    section = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M)
    if not section:
        return []
    rows = [line for line in section.group(1).splitlines() if line.startswith("|")]
    return [[cell.strip() for cell in row.strip("|").split("|")] for row in rows[2:]]


def read_curriculum():
    text = CURRICULUM.read_text(encoding="utf-8") if CURRICULUM.exists() else ""
    topics = []
    for row in table_rows(text, "Topics"):
        if len(row) >= 7:
            topics.append({"order": int(row[0]), "id": row[1], "unit": row[2], "level": row[3],
                           "group": row[4], "name": row[5], "pitfall": row[6]})
    tags = {row[0]: row[1] for row in table_rows(text, "Error tags (Hata etiketleri)") if len(row) >= 2}
    return topics, tags


def esc(value):
    return html.escape(str(value))


def pct(rows):
    return 100 * sum(POINTS[a["result"]] for a in rows) / len(rows) if rows else 0


def topic_status(rows, seen, last_day, today):
    # Kurallar SKILL.md § 7 ile aynı: ✅ = 1, 🟡 = 0.5, ❌ = 0.
    if not rows:
        return "learning" if seen else "new"
    if len(rows) < 4:
        return "learning"
    if pct(rows[-5:]) < 50:
        return "weak"
    days = len({a["date"] for a in rows})
    production_ok = sum(1 for a in rows if a.get("qtype") in PRODUCTION and a["result"] == "ok")
    if pct(rows[-10:]) >= 80 and days >= 2 and production_ok >= 2:
        if (today - date.fromisoformat(last_day)).days > REVIEW_AFTER_DAYS:
            return "review"
        return "good"
    return "developing"


def topic_stats(answers, topics, today):
    stats = []
    for t in topics:
        all_rows = [a for a in answers if a.get("topic_id") == t["id"] and a.get("kind") != WORK_KIND]
        rows = [a for a in all_rows if a.get("result") in POINTS]
        last_day = max((a["date"] for a in all_rows), default="")
        trend = "—"
        if len(rows) >= 6:
            diff = pct(rows[-5:]) - pct(rows[-10:-5])
            trend = "↑" if diff >= 15 else "↓" if diff <= -15 else "→"
        stats.append({**t, "n": len(rows), "score": round(pct(rows[-10:])) if rows else None,
                      "dots": "".join(DOTS[a["result"]] for a in rows[-10:]), "trend": trend, "last": last_day,
                      "status": topic_status(rows, bool(all_rows), last_day, today)})
    return stats


def stacked_bars(days, counts):
    # Günlük cevaplar: doğru / yakın / yanlış yığılmış çubuk; her bölüm arasında 2px boşluk.
    width, height, left, bottom, top = 640, 220, 32, 28, 12
    plot_h = height - bottom - top
    peak = max([sum(counts[d].values()) for d in days] + [1])
    step = (width - left - 8) / max(len(days), 1)
    bar_w = min(28, step * 0.6)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Günlük cevaplar">']
    for tick in range(0, peak + 1, max(1, peak // 4)):
        y = top + plot_h - tick / peak * plot_h
        parts.append(f'<line x1="{left}" x2="{width}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                     f'<text x="{left - 6}" y="{y + 4:.1f}" class="axis" text-anchor="end">{tick}</text>')
    for i, day in enumerate(days):
        x = left + i * step + (step - bar_w) / 2
        y = top + plot_h
        for key, label in RESULTS:
            value = counts[day].get(key, 0)
            if not value:
                continue
            h = value / peak * plot_h
            y -= h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{max(h - 2, 1):.1f}" rx="3" class="r-{key}">'
                         f'<title>{esc(day)} · {esc(label)}: {value}</title></rect>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{height - 8}" class="axis" text-anchor="middle">{esc(day[5:])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def line_chart(points, label, suffix="", fixed_max=None):
    # Tek seri çizgi; her noktada üzerine gelince değer görünür.
    width, height, left, bottom, top = 640, 200, 36, 28, 14
    if not points:
        return '<p class="muted">Henüz veri yok.</p>'
    plot_h = height - bottom - top
    peak = fixed_max or max(max(v for _, v in points), 1)
    step = (width - left - 16) / max(len(points) - 1, 1)
    coords = [(left + i * step, top + plot_h - v / peak * plot_h) for i, (_, v) in enumerate(points)]
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}">']
    for tick in (0, peak / 2, peak):
        y = top + plot_h - tick / peak * plot_h
        parts.append(f'<line x1="{left}" x2="{width}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                     f'<text x="{left - 6}" y="{y + 4:.1f}" class="axis" text-anchor="end">{tick:.0f}{suffix}</text>')
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(coords))
    parts.append(f'<path d="{path}" class="line"/>')
    for (x, y), (day, value) in zip(coords, points):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="dot"><title>{esc(day)} · {esc(label)}: {value:.0f}{suffix}</title></circle>')
    first, last = points[0][0], points[-1][0]
    parts.append(f'<text x="{coords[0][0]:.1f}" y="{height - 8}" class="axis" text-anchor="start">{esc(first[5:])}</text>')
    if last != first:
        parts.append(f'<text x="{coords[-1][0]:.1f}" y="{height - 8}" class="axis" text-anchor="end">{esc(last[5:])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def badge(status):
    return f'<span class="badge s-{status}">{esc(STATUS_LABEL[status])}</span>'


def level_meter(level, stats):
    # Seviye ilerlemesi: iyi / gelişiyor / kalan, tek çubuk; bölümler arasında 2px boşluk.
    rows = [s for s in stats if s["level"] == level]
    good = sum(1 for s in rows if s["status"] in ("good", "review"))
    developing = sum(1 for s in rows if s["status"] == "developing")
    segments = segment_bar(len(rows), [("good", STATUS_LABEL["good"], good),
                                       ("developing", STATUS_LABEL["developing"], developing)])
    return (f'<div class="meter-row"><div class="meter-label"><b>{esc(level)}</b> · {good} / {len(rows)} konu iyi'
            f' · {developing} gelişiyor</div><div class="meter">{segments}</div></div>')


def segment_bar(total, parts):
    total = total or 1
    return "".join(
        f'<i class="seg s-{key}" style="width:{100 * value / total:.1f}%" title="{esc(label)}: {value}"></i>'
        for key, label, value in parts if value)


def xp_total(answers):
    total = 0
    for a in answers:
        if a.get("kind") == WORK_KIND:
            continue
        total += XP_RESULT.get(a.get("result"), XP_KIND.get(a.get("kind"), 0))
    return total


def xp_level(xp):
    # Her seviye bir öncekinden 50 XP daha fazla ister: 100, 150, 200 …
    level, need = 1, 100
    while xp >= need:
        xp -= need
        level += 1
        need += 50
    return level, xp, need


def road_html(stats):
    # Müfredat yolu: 🟢 konu = 1, 🟠 = 0,5; A1 yolun ilk yarısı, A2 ikinci yarısı.
    weight = {"good": 1, "review": 1, "developing": 0.5}
    position = 0
    for level in ("A1", "A2"):
        rows = [s for s in stats if s["level"] == level]
        if rows:
            position += 50 * sum(weight.get(s["status"], 0) for s in rows) / len(rows)
    pin = min(max(position, 10), 90)
    stops = "".join(f'<span class="stop" style="left:{x}%">{name}</span>' for x, name in ((0, "A1"), (50, "A2"), (100, "B1")))
    return (f'<div class="road-pin" style="left:{pin:.1f}%">📍 Sen buradasın · %{position:.0f}</div>'
            f'<div class="road"><i class="road-fill" style="width:{position:.1f}%"></i>'
            f'<i class="road-mark" style="left:50%"></i></div><div class="road-stops">{stops}</div>'
            f'<p class="muted small">🟢 konu tam puan, 🟠 konu yarım puan sayılır. A1 konuları bitince A2 durağına varırsın.</p>')


def ring_svg(value, goal):
    size, radius = 120, 48
    length = 2 * 3.14159 * radius
    filled = min(value / goal, 1) * length if goal else 0
    return (f'<svg viewBox="0 0 {size} {size}" class="ring" role="img" aria-label="Haftalık hedef">'
            f'<circle cx="60" cy="60" r="{radius}" class="ring-bg"/>'
            f'<circle cx="60" cy="60" r="{radius}" class="ring-fill" stroke-dasharray="{filled:.1f} {length:.1f}"'
            f' transform="rotate(-90 60 60)"><title>Bu hafta: {value} / {goal}</title></circle>'
            f'<text x="60" y="58" text-anchor="middle" class="ring-num">{value}</text>'
            f'<text x="60" y="78" text-anchor="middle" class="axis">/ {goal} soru</text></svg>')


def calendar_svg(activity, today):
    # Son 12 hafta, GitHub gibi: sütun = hafta, satır = gün; koyu = çok kayıt.
    cell, gap, left = 14, 3, 30
    start = today - timedelta(days=today.weekday() + 7 * (CALENDAR_WEEKS - 1))
    width = left + CALENDAR_WEEKS * (cell + gap)
    height = 7 * (cell + gap) + 18
    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" class="cal" role="img" aria-label="Çalışma takvimi">']
    for row, name in ((0, "Pzt"), (2, "Çar"), (4, "Cum")):
        parts.append(f'<text x="0" y="{row * (cell + gap) + 11}" class="axis">{name}</text>')
    for week in range(CALENDAR_WEEKS):
        monday = start + timedelta(days=7 * week)
        if monday.day <= 7:
            parts.append(f'<text x="{left + week * (cell + gap)}" y="{height - 2}" class="axis">{monday:%m}.ay</text>')
        for row in range(7):
            day = monday + timedelta(days=row)
            if day > today:
                continue
            n = activity.get(day.isoformat(), 0)
            step = 0 if n == 0 else 1 if n <= 3 else 2 if n <= 9 else 3 if n <= 19 else 4
            parts.append(f'<rect x="{left + week * (cell + gap)}" y="{row * (cell + gap)}" width="{cell}" height="{cell}"'
                         f' rx="3" class="c{step}"><title>{day.isoformat()} · {n} kayıt</title></rect>')
    parts.append("</svg>")
    return "".join(parts)


def sparkline(values, labels, name):
    width, height, pad = 220, 56, 6
    peak = max(values + [1])
    step = (width - 2 * pad) / max(len(values) - 1, 1)
    coords = [(pad + i * step, height - pad - v / peak * (height - 2 * pad)) for i, v in enumerate(values)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(coords))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="dot"><title>{esc(name)} · {esc(label)} haftası: {v}</title></circle>'
                   for (x, y), v, label in zip(coords, values, labels))
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(name)} haftalık">'
            f'<line x1="0" x2="{width}" y1="{height - pad}" y2="{height - pad}" class="grid"/>'
            f'<path d="{path}" class="line"/>{dots}</svg>')


def longest_streak(active_days):
    best, run, previous = 0, 0, None
    for d in active_days:
        day = date.fromisoformat(d)
        run = run + 1 if previous and (day - previous).days == 1 else 1
        best = max(best, run)
        previous = day
    return best


def skill_verdict(score, n):
    if n < 3:
        return "learning", "🔵 Az veri"
    if score < 60:
        return "weak", "🔴 Zorlanıyorsun"
    if score < 80:
        return "developing", "🟠 Gelişiyor"
    return "good", "🟢 İyi"


def clean_example(topic):
    text = re.sub(r"^sınav-\d+:\s*", "", topic or "")
    return text if len(text) <= 90 else text[:87] + "…"


def main():
    answers = read_answers()
    progress = PROGRESS.read_text(encoding="utf-8") if PROGRESS.exists() else ""
    topics, tags = read_curriculum()
    words = table_rows(progress, "Yeni kelimeler ve kalıplar")
    cards = table_rows(progress, "Tekrar listesi")
    tips = table_rows(progress, "Hap bilgiler")
    today = date.today()

    graded = [a for a in answers if a.get("result") in POINTS and a.get("kind") != WORK_KIND]
    correct = sum(1 for a in graded if a["result"] == "ok")
    accuracy = round(100 * correct / len(graded)) if graded else 0
    reviews = sum(1 for a in answers if a.get("kind") in ("review", "tip-check"))
    due = sum(1 for c in cards if len(c) > 2 and c[2] and c[2] <= today.isoformat())
    active_days = sorted({a["date"] for a in answers})
    streak = 0
    day = today
    while day.isoformat() in active_days:
        streak += 1
        day -= timedelta(days=1)

    days = active_days[-21:]
    counts = OrderedDict((d, {}) for d in days)
    for a in graded:
        if a["date"] in counts:
            counts[a["date"]][a["result"]] = counts[a["date"]].get(a["result"], 0) + 1

    word_dates = sorted(w[2] for w in words if len(w) > 2 and re.match(r"\d{4}-\d{2}-\d{2}", w[2]))
    cumulative, running = [], 0
    for d in sorted(set(word_dates)):
        running += word_dates.count(d)
        cumulative.append((d, running))

    rolling = []
    for d in days:
        upto = [a for a in graded if a["date"] <= d][-10:]
        if upto:
            rolling.append((d, pct(upto)))

    stats = topic_stats(answers, topics, today)
    by_status = {key: [s for s in stats if s["status"] == key] for key, _ in STATUSES}
    next_topic = next((s for s in stats if s["status"] in ("new", "learning")), None)
    done = ("good", "review")
    work_level = next((lv for lv in ("A1", "A2") if any(s["status"] not in done for s in stats if s["level"] == lv)), "A2 ✓")
    current_unit = next_topic["unit"] if next_topic else "1"

    error_all, error_recent = Counter(), Counter()
    recent_from = (today - timedelta(days=14)).isoformat()
    for a in answers:
        for tag in filter(None, (a.get("errors") or "").split(";")):
            error_all[tag] += 1
            if a["date"] >= recent_from:
                error_recent[tag] += 1

    exams = OrderedDict()
    for a in graded:
        match = re.match(r"(sınav-\d+)", a.get("topic") or "")
        if a.get("kind") == "exam" and match:
            exams.setdefault(match.group(1), []).append(a)

    # --- Oyun ve motivasyon ---
    xp = xp_total(answers)
    level_no, level_xp, level_need = xp_level(xp)
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)
    this_week = sum(1 for a in graded if a["date"] >= week_start.isoformat())
    last_week = sum(1 for a in graded if last_week_start.isoformat() <= a["date"] < week_start.isoformat())
    activity = Counter(a["date"] for a in answers)
    best_streak = longest_streak(active_days)
    best_run, run = 0, 0
    for a in graded:
        run = run + 1 if a["result"] == "ok" else 0
        best_run = max(best_run, run)
    best_exam = max((round(pct(rows)) for rows in exams.values()), default=0)
    good_topics = len(by_status["good"]) + len(by_status["review"])
    units_done = sum(1 for unit in {s["unit"] for s in stats if s["unit"] != "K"}
                     if all(s["status"] in done for s in stats if s["unit"] == unit))

    tomorrow = (today + timedelta(days=1)).isoformat()
    card_dates = [c[2] for c in cards if len(c) > 2 and re.match(r"\d{4}-\d{2}-\d{2}", c[2])]
    card_parts = [
        ("overdue", "Gecikmiş", sum(1 for d in card_dates if d < today.isoformat())),
        ("today", "Bugün", sum(1 for d in card_dates if d == today.isoformat())),
        ("tomorrow", "Yarın", sum(1 for d in card_dates if d == tomorrow)),
        ("later", "Sonra", sum(1 for d in card_dates if d > tomorrow)),
    ]

    trend_weeks = [week_start - timedelta(days=7 * i) for i in range(TREND_WEEKS - 1, -1, -1)]
    trend_tags = [t for t, _ in error_all.most_common() if t != MINOR_TAG][:3]
    trends = []
    for tag in trend_tags:
        tagged = [a["date"] for a in answers if tag in (a.get("errors") or "").split(";")]
        values = [sum(1 for d in tagged if w.isoformat() <= d < (w + timedelta(days=7)).isoformat()) for w in trend_weeks]
        trends.append((tag, values))

    vocab_ids = {s["id"] for s in stats if s["group"] == "Kelime"}
    vocab_rows = [a for a in graded if a.get("topic_id") in vocab_ids]
    skill_rows = [(name, [a for a in graded if a.get("qtype") in types]) for name, types in SKILLS]
    skill_rows += [("Gramer", [a for a in graded if a.get("area") == "Gramer"]), ("Kelime", vocab_rows)]
    skills = []
    for name, rows in skill_rows:
        recent = rows[-SKILL_WINDOW:]
        score = round(pct(recent))
        key, label = skill_verdict(score, len(recent))
        skills.append({"name": name, "n": len(recent), "score": score, "key": key, "label": label})
    skills.sort(key=lambda s: (s["key"] == "learning", s["score"]))

    # --- HTML parçaları ---
    tiles = [
        ("Çalışma seviyesi / Level", esc(work_level)),
        ("İyi konu / Topics good", f"{len(by_status['good']) + len(by_status['review'])} / {len(stats)}"),
        ("Puan / Score", f"{round(pct(graded))}%"),
        ("Kelime / Words", len(words)),
        ("Bugün tekrar / Due today", due),
    ]
    extra_tiles = [
        ("Toplam soru / Questions", len(graded)),
        ("Tam doğru / Correct", f"{accuracy}%"),
        ("Seri / Streak", f"{streak} gün"),
    ]
    def tile_row(items):
        return "".join(f'<div class="tile"><div class="tlabel">{esc(t)}</div><div class="tvalue">{v}</div></div>' for t, v in items)

    tile_html = tile_row(tiles)

    def names(items, limit=None):
        shown = items[:limit] if limit else items
        if not shown:
            return '<p class="muted">—</p>'
        extra = f'<li class="muted">+{len(items) - len(shown)} konu daha</li>' if len(items) > len(shown) else ""
        return "<ul>" + "".join(f"<li>{esc(s['name'])}</li>" for s in shown) + extra + "</ul>"

    summary_cols = [
        ("good", "Bu konularda iyisin", by_status["good"], None),
        ("developing", "Kendini geliştiriyorsun", by_status["developing"], None),
        ("weak", "Zayıfsın, çalışmalısın", by_status["weak"], None),
        ("review", "Tekrar zamanı (unutmadan)", by_status["review"], None),
        ("learning", "Öğreniliyor (az cevap)", by_status["learning"], 8),
        ("new", "Henüz başlamadın", by_status["new"], 6),
    ]
    summary_html = "".join(
        f'<div class="sum s-{key}"><div class="sum-head">{esc(STATUS_LABEL[key])} · {len(items)}</div>'
        f'<div class="muted small">{esc(title)}</div>{names(items, limit)}</div>'
        for key, title, items, limit in summary_cols if items or key == "good")

    notes = []
    if next_topic:
        notes.append(f"Sıradaki konu: <b>{esc(next_topic['name'])}</b> (Ünite {esc(next_topic['unit'])}).")
    if by_status["weak"]:
        notes.append("En çok çalışman gereken: " + ", ".join(f"<b>{esc(s['name'])}</b>" for s in by_status["weak"]) + ".")
    if by_status["review"]:
        notes.append("Unutmaya başlayabilirsin, tekrar et: " + ", ".join(esc(s["name"]) for s in by_status["review"]) + ".")
    main_recent = [(tag, n) for tag, n in error_recent.most_common() if tag != MINOR_TAG]
    if main_recent:
        top_tag, top_count = main_recent[0]
        notes.append(f"Son 14 günde en sık hatan: <b>{esc(tags.get(top_tag, top_tag))}</b> ({top_count} kez).")
    hardest = next((s for s in skills if s["key"] == "weak"), None)
    if hardest:
        notes.append(f"En çok zorlandığın yön: <b>{esc(hardest['name'])}</b> (%{hardest['score']}).")
    notes_html = "".join(f"<li>{n}</li>" for n in notes) or '<li class="muted">Henüz veri yok.</li>'

    level_html = "".join(level_meter(level, stats) for level in ("A1", "A2"))

    week_from = (today - timedelta(days=7)).isoformat()
    word_groups = Counter(w[3] if len(w) > 3 and w[3] else "Temel" for w in words)
    week_words = sum(1 for w in words if len(w) > 2 and w[2] >= week_from)
    vocab_cells = "".join(f"<li>{esc(g)}: <b>{n}</b></li>" for g, n in word_groups.most_common())
    vocab_html = (f"<p>Toplam <b>{len(words)}</b> kelime ve kalıp · son 7 günde <b>+{week_words}</b>"
                  f" · kelime sorularında puan: <b>{str(round(pct(vocab_rows))) + '%' if vocab_rows else '—'}</b></p>"
                  f"<ul class='notes'>{vocab_cells}</ul>")
    level_legend = "".join(f'<span class="key"><i class="sw s-{k}"></i>{esc(STATUS_LABEL[k][2:])}</span>' for k in ("good", "developing"))

    group_rows = ""
    for g in GROUPS:
        rows = [s for s in stats if s["group"] == g]
        cells = "".join(f"<td>{sum(1 for s in rows if s['status'] == key) or ''}</td>" for key, _ in STATUSES)
        group_rows += f"<tr><td>{esc(g)}</td><td>{len(rows)}</td>{cells}</tr>"
    group_head = "".join(f"<th>{esc(label)}</th>" for _, label in STATUSES)

    unit_html = ""
    for unit in sorted({s["unit"] for s in stats}, key=lambda u: (not u.isdigit(), u.zfill(3))):
        rows = [s for s in stats if s["unit"] == unit]
        good = sum(1 for s in rows if s["status"] in ("good", "review"))
        body = "".join(
            f"<tr title='Tipik hata: {esc(s['pitfall'])}'><td>{esc(s['name'])}</td><td>{badge(s['status'])}</td>"
            f"<td>{'' if s['score'] is None else str(s['score']) + '%'}</td><td class='dots'>{s['dots']}</td>"
            f"<td>{esc(s['trend'])}</td></tr>"
            for s in rows)
        unit_html += (f"<details class='card unit' {'open' if unit == current_unit else ''}><summary><b>{'Kelime yolları / Vocabulary tracks' if unit == 'K' else 'Ünite ' + esc(unit)}</b>"
                      f" · {good} / {len(rows)} iyi</summary><div class='scroll'><table><tr><th>Konu</th>"
                      f"<th>Durum</th><th>Puan</th><th>Son 10</th><th>Trend</th></tr>{body}</table></div></details>")

    ranked = [(t, n) for t, n in error_all.most_common() if t != MINOR_TAG]
    peak_error = max([n for _, n in ranked], default=1)
    def examples(tag):
        found = [clean_example(a.get("topic")) for a in reversed(answers) if tag in (a.get("errors") or "").split(";")]
        return "".join(f"<div>{esc(e)}</div>" for e in found[:2])

    error_rows = "".join(
        f"<tr><td>{esc(tags.get(tag, tag))}</td><td class='barcell'><div class='hbar' style='width:{100 * n / peak_error:.0f}%'"
        f" title='{esc(tags.get(tag, tag))}: {n}'></div></td><td>{n}</td><td>{error_recent.get(tag, 0)}</td>"
        f"<td class='small muted'>{examples(tag)}</td></tr>"
        for tag, n in ranked)
    if error_all.get(MINOR_TAG):
        error_rows += (f"<tr class='muted'><td>{esc(tags.get(MINOR_TAG, MINOR_TAG))} (küçük hata, sadece dikkat)</td><td></td>"
                       f"<td>{error_all[MINOR_TAG]}</td><td>{error_recent.get(MINOR_TAG, 0)}</td><td></td></tr>")
    error_html = (f"<table><tr><th>Hata türü</th><th></th><th>Toplam</th><th>Son 14 gün</th><th>Son örneklerin</th></tr>{error_rows}</table>"
                  if error_rows else '<p class="muted">Henüz veri yok.</p>')

    skill_body = "".join(
        f"<tr><td>{esc(s['name'])}</td><td class='barcell'><div class='hbar v-{s['key']}' style='width:{max(s['score'], 2)}%'"
        f" title='{esc(s['name'])}: %{s['score']}'></div></td><td>%{s['score']}</td><td>{s['n']}</td><td>{esc(s['label'])}</td></tr>"
        for s in skills)
    skill_html = (f"<table><tr><th>Yön</th><th></th><th>Puan</th><th>Cevap</th><th>Durum</th></tr>{skill_body}</table>"
                  f"<p class='muted small'>Her yön için son {SKILL_WINDOW} cevap. %60 altı = zorlanıyorsun, %80 üstü = iyi.</p>")

    trend_html = ""
    week_labels = [f"{w:%d.%m}" for w in trend_weeks]
    for tag, values in trends:
        change = values[-1] - values[-2]
        word = "↓ azalıyor 👏" if change < 0 else "↑ artıyor" if change > 0 else "→ aynı"
        trend_html += (f"<div class='card'><b>{esc(tags.get(tag, tag))}</b>{sparkline(values, week_labels, tags.get(tag, tag))}"
                       f"<div class='small muted'>bu hafta {values[-1]} · geçen hafta {values[-2]} · {word}</div></div>")
    trend_html = trend_html or '<p class="muted">Henüz veri yok.</p>'

    xp_html = (f"<div class='xp-level'>⭐ Level {level_no}</div>"
               f"<div class='meter'><i class='seg s-xp' style='width:{100 * level_xp / level_need:.1f}%'></i></div>"
               f"<div class='small muted'>{level_xp} / {level_need} XP · sonraki seviyeye {level_need - level_xp} XP · toplam {xp} XP</div>"
               f"<div class='small muted'>✅ 10 · 🟡 5 · ❌ 2 (denemek de sayılır) · ders 5 · hap 2</div>")

    goal_note = "🎉 Hedef tamam!" if this_week >= WEEKLY_GOAL else f"Hedefe {WEEKLY_GOAL - this_week} soru kaldı."
    goal_html = (f"<div class='goal'>{ring_svg(this_week, WEEKLY_GOAL)}<div><b>{goal_note}</b>"
                 f"<div class='small muted'>Geçen hafta: {last_week} soru</div>"
                 f"<div class='small muted'>Hafta pazartesi başlar.</div></div></div>")

    card_legend = "".join(f'<span class="key"><i class="sw k-{k}"></i>{esc(label)}: <b>{n}</b></span>' for k, label, n in card_parts)
    card_segments = "".join(f'<i class="seg k-{k}" style="width:{100 * n / (len(card_dates) or 1):.1f}%" title="{esc(label)}: {n}"></i>'
                            for k, label, n in card_parts if n)
    cards_html = (f"<div class='small muted'>Toplam {len(card_dates)} kart</div>"
                  f"<div class='meter tall'>{card_segments}</div><div class='legend'>{card_legend}</div>")

    scale = "".join(f"<i class='sw c{i}'></i>" for i in range(5))
    calendar_html = (f"<div class='scroll'>{calendar_svg(activity, today)}</div>"
                     f"<div class='legend'><span>az</span>{scale}<span>çok</span>"
                     f"<span class='key'>🔥 Şu anki seri: <b>{streak} gün</b></span><span class='key'>🏆 En uzun seri: <b>{best_streak} gün</b></span></div>")

    unit_cards = ""
    for unit in sorted({s["unit"] for s in stats}, key=lambda u: (not u.isdigit(), u.zfill(3))):
        rows = [s for s in stats if s["unit"] == unit]
        good = sum(1 for s in rows if s["status"] in done)
        developing = sum(1 for s in rows if s["status"] in ("developing", "weak"))
        learning = sum(1 for s in rows if s["status"] == "learning")
        icon = "✅" if good == len(rows) else "▶️" if unit == current_unit else "🗺️"
        title = f"Ünite {unit}" if unit != "K" else "Kelime"
        bar = segment_bar(len(rows), [("good", "İyi", good), ("developing", "Gelişiyor", developing), ("learning", "Öğreniliyor", learning)])
        unit_cards += (f"<div class='card unit-card{' current' if unit == current_unit else ''}'><div>{icon} <b>{esc(title)}</b></div>"
                       f"<div class='small muted'>{esc(UNIT_NAMES.get(unit, ''))}</div><div class='meter'>{bar}</div>"
                       f"<div class='small muted'>{good} / {len(rows)} iyi</div></div>")
    unit_legend = "".join(f'<span class="key"><i class="sw s-{k}"></i>{label}</span>'
                          for k, label in (("good", "İyi"), ("developing", "Gelişiyor / zayıf"), ("learning", "Öğreniliyor")))

    badges = [
        ("🌱", "İlk adım", "ilk cevap", len(graded), 1),
        ("📝", "50 soru", "50 cevap", len(graded), 50),
        ("💯", "100 soru", "100 cevap", len(graded), 100),
        ("🔥", "3 gün seri", "3 gün üst üste", best_streak, 3),
        ("🏆", "7 gün seri", "7 gün üst üste", best_streak, 7),
        ("🎯", "5'te 5", "5 doğru üst üste", best_run, 5),
        ("⚡", "10'da 10", "10 doğru üst üste", best_run, 10),
        ("🎓", "İlk sınav", "bir ünite sınavı", len(exams), 1),
        ("🥇", "Sınav yıldızı", "sınavda %80+", best_exam, 80),
        ("📘", "25 kelime", "25 kelime ve kalıp", len(words), 25),
        ("📚", "50 kelime", "50 kelime ve kalıp", len(words), 50),
        ("🟢", "İlk iyi konu", "bir konu 🟢", good_topics, 1),
        ("🗺️", "Ünite bitti", "bir ünitenin tüm konuları 🟢", units_done, 1),
        ("⭐", "Level 5", "5. seviye XP", level_no, 5),
    ]
    unlocked = sum(1 for *_, value, target in badges if value >= target)
    badge_html = "".join(
        f"<div class='badge-card{'' if value >= target else ' locked'}' title='{esc(desc)}'>"
        f"<div class='badge-icon'>{icon if value >= target else '🔒'}</div><b>{esc(name)}</b>"
        f"<div class='small muted'>{esc(desc)}</div><div class='small muted'>{'✓ açıldı' if value >= target else f'{min(value, target)} / {target}'}</div></div>"
        for icon, name, desc, value, target in badges)

    exam_rows = ""
    for name, rows in exams.items():
        result = Counter(a["result"] for a in rows)
        per_topic = OrderedDict()
        for a in rows:
            per_topic.setdefault(a.get("topic_id") or "—", []).append(DOTS[a["result"]])
        topic_names = {s["id"]: s["name"] for s in stats}
        detail = "; ".join(f"{esc(topic_names.get(k, k))} {''.join(v)}" for k, v in per_topic.items())
        exam_rows += (f"<tr><td>{esc(name)}</td><td>{esc(rows[0]['date'])}</td><td>{result['ok']}</td><td>{result['close']}</td>"
                      f"<td>{result['wrong']}</td><td>{round(pct(rows))}%</td><td class='small'>{detail}</td></tr>")
    exam_html = (f"<table><tr><th>Sınav</th><th>Tarih</th><th>✅</th><th>🟡</th><th>❌</th><th>Puan</th><th>Konular</th></tr>{exam_rows}</table>"
                 if exam_rows else '<p class="muted">Henüz sınav yok.</p>')

    area_rows = ""
    for area in AREAS:
        rows = [a for a in graded if a.get("area") == area]
        ok = sum(1 for a in rows if a["result"] == "ok")
        area_rows += f"<tr><td>{esc(area)}</td><td>{len(rows)}</td><td>{ok}</td><td>{round(pct(rows)) if rows else '—'}{'%' if rows else ''}</td></tr>"

    legend = "".join(f'<span class="key"><i class="sw r-{k}"></i>{esc(l)}</span>' for k, l in RESULTS)
    day_rows = "".join(
        f"<tr><td>{esc(d)}</td><td>{counts[d].get('ok', 0)}</td><td>{counts[d].get('close', 0)}</td><td>{counts[d].get('wrong', 0)}</td></tr>"
        for d in reversed(days))

    page = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>English Progress</title>
<style>
:root {{ color-scheme: light; --surface:#fcfcfb; --card:#ffffff; --border:#e4e3df; --text:#0b0b0b; --muted:#52514e;
  --grid:#e9e8e4; --series:#2a78d6; --ok:#0ca30c; --close:#fab219; --wrong:#d03b3b; --serious:#ec835a; --none:#c3c2b7; }}
@media (prefers-color-scheme: dark) {{ :root:where(:not([data-theme="light"])) {{ color-scheme: dark; --surface:#1a1a19; --card:#232322;
  --border:#3a3a38; --text:#ffffff; --muted:#c3c2b7; --grid:#33332f; --series:#3987e5; --none:#52514e; }} }}
:root[data-theme="dark"] {{ color-scheme: dark; --surface:#1a1a19; --card:#232322; --border:#3a3a38; --text:#ffffff; --muted:#c3c2b7;
  --grid:#33332f; --series:#3987e5; --none:#52514e; }}
body {{ margin:0; background:var(--surface); color:var(--text); font:15px/1.5 -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width:960px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ font-size:24px; margin:0 0 4px; }} h2 {{ font-size:17px; margin:28px 0 8px; }}
.muted {{ color:var(--muted); }} .small {{ font-size:12px; }}
.tiles {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:10px; margin-top:16px; }}
.tile {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:12px 14px; }}
.tlabel {{ color:var(--muted); font-size:13px; }} .tvalue {{ font-size:26px; font-weight:600; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:12px 14px; }}
.unit {{ margin-bottom:10px; }} .unit summary {{ color:var(--text); font-size:15px; }}
.scroll {{ overflow-x:auto; }}
.sums {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:10px; }}
.sum {{ background:var(--card); border:1px solid var(--border); border-left-width:5px; border-radius:10px; padding:10px 14px; }}
.sum ul {{ margin:6px 0 0; padding-left:18px; }} .sum-head {{ font-weight:600; }}
.sum.s-good {{ border-left-color:var(--ok); }} .sum.s-developing {{ border-left-color:var(--close); }}
.sum.s-weak {{ border-left-color:var(--wrong); }} .sum.s-review {{ border-left-color:var(--serious); }}
.sum.s-learning {{ border-left-color:var(--series); }} .sum.s-new {{ border-left-color:var(--none); }}
.badge {{ white-space:nowrap; font-size:13px; }}
.meter-row {{ margin:8px 0 12px; }} .meter-label {{ font-size:14px; margin-bottom:4px; }}
.meter {{ display:flex; gap:2px; height:14px; background:var(--grid); border-radius:4px; overflow:hidden; }}
.seg {{ display:block; height:100%; }}
.seg.s-good, .sw.s-good {{ background:var(--ok); }} .seg.s-developing, .sw.s-developing {{ background:var(--close); }}
.hbar {{ height:12px; background:var(--series); border-radius:0 4px 4px 0; min-width:2px; }} .barcell {{ width:45%; }}
.dots {{ white-space:nowrap; font-size:12px; letter-spacing:-1px; }}
svg {{ width:100%; height:auto; display:block; }}
.grid {{ stroke:var(--grid); stroke-width:1; }} .axis {{ fill:var(--muted); font-size:11px; }}
.line {{ fill:none; stroke:var(--series); stroke-width:2; }} .dot {{ fill:var(--series); stroke:var(--card); stroke-width:2; }}
.r-ok {{ fill:var(--ok); background:var(--ok); }} .r-close {{ fill:var(--close); background:var(--close); }} .r-wrong {{ fill:var(--wrong); background:var(--wrong); }}
.legend {{ display:flex; gap:16px; flex-wrap:wrap; font-size:13px; color:var(--muted); margin-bottom:6px; }}
.key {{ display:inline-flex; align-items:center; gap:6px; }} .sw {{ width:12px; height:12px; border-radius:3px; display:inline-block; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }} td, th {{ text-align:left; padding:6px 8px; border-bottom:1px solid var(--border); vertical-align:top; }}
th {{ color:var(--muted); font-weight:500; }}
.notes {{ margin:0; padding-left:20px; }}
details {{ margin-top:8px; }} summary {{ cursor:pointer; color:var(--muted); font-size:13px; }}
h3 {{ font-size:15px; margin:0 0 8px; }}
.hero, .pair {{ display:grid; grid-template-columns:2fr 1fr; gap:10px; margin-top:16px; }}
.pair {{ grid-template-columns:1fr 1fr; margin-top:0; }}
@media (max-width:640px) {{ .hero, .pair {{ grid-template-columns:1fr; }} }}
.road-wrap {{ position:relative; padding-top:30px; }}
.road-pin {{ position:absolute; top:0; transform:translateX(-50%); white-space:nowrap; font-weight:600; font-size:14px; }}
.road {{ position:relative; height:16px; background:var(--grid); border-radius:8px; }}
.road-fill {{ position:absolute; left:0; top:0; bottom:0; background:var(--series); border-radius:8px; }}
.road-mark {{ position:absolute; top:-4px; bottom:-4px; width:2px; background:var(--muted); }}
.road-stops {{ position:relative; height:22px; font-weight:600; font-size:13px; }}
.stop {{ position:absolute; top:4px; transform:translateX(-50%); }}
.stop:first-child {{ transform:none; }} .stop:last-child {{ transform:translateX(-100%); }}
.xp-level {{ font-size:22px; font-weight:700; margin-bottom:6px; }}
.seg.s-xp, .seg.s-learning, .sw.s-learning {{ background:var(--series); }}
.meter.tall {{ height:20px; margin:6px 0 8px; }}
.k-overdue {{ background:var(--wrong); }} .k-today {{ background:var(--close); }}
.k-tomorrow {{ background:var(--series); }} .k-later {{ background:var(--none); }}
.goal {{ display:flex; gap:16px; align-items:center; margin-top:6px; }}
svg.ring {{ width:120px; height:120px; flex:none; }}
.ring-bg {{ fill:none; stroke:var(--grid); stroke-width:12; }}
.ring-fill {{ fill:none; stroke:var(--series); stroke-width:12; stroke-linecap:round; }}
.ring-num {{ fill:var(--text); font-size:28px; font-weight:600; }}
svg.cal {{ width:auto; max-width:100%; }}
.cal .c0, .sw.c0 {{ fill:var(--grid); background:var(--grid); }}
.cal .c1, .cal .c2, .cal .c3, .cal .c4 {{ fill:var(--series); }}
.sw.c1, .sw.c2, .sw.c3, .sw.c4 {{ background:var(--series); }}
.cal .c1 {{ fill-opacity:.3; }} .cal .c2 {{ fill-opacity:.5; }} .cal .c3 {{ fill-opacity:.75; }}
.sw.c1 {{ opacity:.3; }} .sw.c2 {{ opacity:.5; }} .sw.c3 {{ opacity:.75; }}
.trends {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:10px; }}
.units {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:10px; }}
.unit-card .meter {{ margin:6px 0 4px; }} .unit-card.current {{ border:2px solid var(--series); }}
.badges {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(130px, 1fr)); gap:10px; }}
.badge-card {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:10px; text-align:center; }}
.badge-card.locked {{ opacity:.5; }} .badge-icon {{ font-size:28px; }}
.hbar.v-weak {{ background:var(--wrong); }} .hbar.v-developing {{ background:var(--close); }}
.hbar.v-good {{ background:var(--ok); }} .hbar.v-learning {{ background:var(--none); }}
</style></head>
<body><main>
<h1>English progress · İngilizce ilerleme</h1>
<div class="muted">Güncellendi / Updated: {datetime.now():%Y-%m-%d %H:%M} · Müfredat: A1–A2 · Puan: ✅ = 1, 🟡 = 0,5, ❌ = 0</div>
<div class="hero">
<div class="card"><h3>Seviye yolu / Level road</h3><div class="road-wrap">{road_html(stats)}</div></div>
<div class="card"><h3>XP / Oyun puanı</h3>{xp_html}</div>
</div>
<div class="tiles">{tile_html}</div>

<h2>Öğretmen notu / Teacher's note</h2>
<div class="card"><ul class="notes">{notes_html}</ul></div>

<h2>Çalışman gereken yönler / What to work on</h2>
<div class="card scroll">{skill_html}</div>

<h2>En sık hatalar / Top mistakes</h2>
<div class="card scroll">{error_html}</div>

<h2>Hata eğilimi / Mistake trend (haftalık)</h2>
<div class="trends">{trend_html}</div>

<h2>Bu hafta / This week</h2>
<div class="pair">
<div class="card"><h3>Haftalık hedef / Weekly goal</h3>{goal_html}</div>
<div class="card"><h3>Tekrar kartları / Review cards</h3>{cards_html}</div>
</div>

<h2>Çalışma takvimi / Study calendar</h2>
<div class="card">{calendar_html}</div>

<h2>Ünite haritası / Unit map</h2>
<div class="card"><div class="legend">{unit_legend}</div><div class="units">{unit_cards}</div></div>

<h2>Rozetler / Badges · {unlocked} / {len(badges)}</h2>
<div class="badges">{badge_html}</div>

<h2>Durumun / Where you are</h2>
<div class="sums">{summary_html}</div>

<h2>Seviye ilerlemesi / Level progress</h2>
<div class="card"><div class="legend">{level_legend}</div>{level_html}</div>

<h2>Kelimeler / Vocabulary</h2>
<div class="card">{vocab_html}</div>

<h2>Konular / Topics</h2>
{unit_html}

<h2>Sınavlar / Exams</h2>
<div class="card scroll">{exam_html}</div>

<h2>Ayrıntılar / More details</h2>
<details class="card"><summary>Grafikler ve tablolar / Charts and tables</summary>
<div class="tiles">{tile_row(extra_tiles)}</div>
<h2>Gruplar / Groups</h2>
<div class="card scroll"><table><tr><th>Grup</th><th>Konu</th>{group_head}</tr>{group_rows}</table></div>

<h2>Günlük cevaplar / Answers per day</h2>
<div class="card"><div class="legend">{legend}</div>{stacked_bars(days, counts) if days else '<p class="muted">Henüz veri yok.</p>'}
<details><summary>Tablo / Table</summary><table><tr><th>Tarih</th><th>✅</th><th>🟡</th><th>❌</th></tr>{day_rows}</table></details></div>

<h2>Puan, son 10 cevap / Score, last 10 answers</h2>
<div class="card">{line_chart(rolling, "Puan", "%", fixed_max=100)}</div>

<h2>Öğrenilen kelime ve kalıp / Words learned (toplam)</h2>
<div class="card">{line_chart(cumulative, "Toplam kelime ve kalıp")}</div>

<h2>Alanlar / Areas</h2>
<div class="card"><table><tr><th>Alan</th><th>Soru</th><th>Doğru</th><th>Puan</th></tr>{area_rows}</table>
<p class="muted small">Hap bilgi: {len(tips)} · Tekrar yapıldı: {reviews}</p></div>
</details>
</main></body></html>"""
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"dashboard: {OUT}")
    # Kısa özet: skill oturum başında konu seçmek için okur.
    for key, label in STATUSES[:5]:
        if by_status[key]:
            print(f"{label}: " + ", ".join(s["id"] for s in by_status[key]))
    print(f"⚪ Başlanmadı: {len(by_status['new'])} konu")
    if next_topic:
        print(f"sıradaki: {next_topic['id']}")
    if main_recent:
        print("son 14 gün hata (yazım hariç): " + ", ".join(f"{tag} {n}" for tag, n in main_recent[:3]))


if __name__ == "__main__":
    main()
