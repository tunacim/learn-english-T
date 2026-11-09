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
    total = len(rows) or 1
    segments = "".join(
        f'<i class="seg s-{key}" style="width:{100 * value / total:.1f}%" title="{esc(label)}: {value}"></i>'
        for key, label, value in (("good", STATUS_LABEL["good"], good), ("developing", STATUS_LABEL["developing"], developing))
        if value)
    return (f'<div class="meter-row"><div class="meter-label"><b>{esc(level)}</b> · {good} / {len(rows)} konu iyi'
            f' · {developing} gelişiyor</div><div class="meter">{segments}</div></div>')


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
    notes_html = "".join(f"<li>{n}</li>" for n in notes) or '<li class="muted">Henüz veri yok.</li>'

    level_html = "".join(level_meter(level, stats) for level in ("A1", "A2"))

    week_from = (today - timedelta(days=7)).isoformat()
    word_groups = Counter(w[3] if len(w) > 3 and w[3] else "Temel" for w in words)
    week_words = sum(1 for w in words if len(w) > 2 and w[2] >= week_from)
    vocab_ids = {s["id"] for s in stats if s["group"] == "Kelime"}
    vocab_rows = [a for a in graded if a.get("topic_id") in vocab_ids]
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
    error_rows = "".join(
        f"<tr><td>{esc(tags.get(tag, tag))}</td><td class='barcell'><div class='hbar' style='width:{100 * n / peak_error:.0f}%'"
        f" title='{esc(tags.get(tag, tag))}: {n}'></div></td><td>{n}</td><td>{error_recent.get(tag, 0)}</td></tr>"
        for tag, n in ranked)
    if error_all.get(MINOR_TAG):
        error_rows += (f"<tr class='muted'><td>{esc(tags.get(MINOR_TAG, MINOR_TAG))} (küçük hata, sadece dikkat)</td><td></td>"
                       f"<td>{error_all[MINOR_TAG]}</td><td>{error_recent.get(MINOR_TAG, 0)}</td></tr>")
    error_html = (f"<table><tr><th>Hata türü</th><th></th><th>Toplam</th><th>Son 14 gün</th></tr>{error_rows}</table>"
                  if error_rows else '<p class="muted">Henüz veri yok.</p>')

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
</style></head>
<body><main>
<h1>English progress · İngilizce ilerleme</h1>
<div class="muted">Güncellendi / Updated: {datetime.now():%Y-%m-%d %H:%M} · Müfredat: A1–A2 · Puan: ✅ = 1, 🟡 = 0,5, ❌ = 0</div>
<div class="tiles">{tile_html}</div>

<h2>Öğretmen notu / Teacher's note</h2>
<div class="card"><ul class="notes">{notes_html}</ul></div>

<h2>Durumun / Where you are</h2>
<div class="sums">{summary_html}</div>

<h2>Seviye ilerlemesi / Level progress</h2>
<div class="card"><div class="legend">{level_legend}</div>{level_html}</div>

<h2>Kelimeler / Vocabulary</h2>
<div class="card">{vocab_html}</div>

<h2>Konular / Topics</h2>
{unit_html}

<h2>En sık hatalar / Top mistakes</h2>
<div class="card">{error_html}</div>

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
