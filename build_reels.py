# -*- coding: utf-8 -*-
"""Строит страницу «Reels дня»: 12 рилсов из копилки reels.json.

Сначала показываются ещё не выходившие ссылки (новые вперёд), затем добираются
самые редко показанные — так дюжина каждый день другая, пока есть запас.
Видео встраиваются официальным плеером Facebook, права остаются у авторов.
"""

import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
REELS = ROOT / "reels.json"
SITE_URL = "https://trainingsw75-cloud.github.io/reels/"
PER_DAY = 12

MSK = timezone(timedelta(hours=3))
MONTHS_RU = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def pick(items):
    # сначала редко показанные, среди равных — новые вперёд
    ordered = sorted(items, key=lambda i: i.get("added", ""), reverse=True)
    ordered = sorted(ordered, key=lambda i: i.get("shown", 0))
    chosen = ordered[:PER_DAY]
    for i in chosen:
        i["shown"] = i.get("shown", 0) + 1
    return chosen


def card(item):
    href = urllib.parse.quote(item["url"], safe="")
    return f"""
    <article class="card">
      <div class="frame">
        <iframe src="https://www.facebook.com/plugins/video.php?href={href}&show_text=false"
                loading="lazy" allow="autoplay; encrypted-media; picture-in-picture"
                allowfullscreen scrolling="no"></iframe>
      </div>
      <a class="open" href="{item['url']}" target="_blank" rel="noopener">Открыть в Facebook ↗</a>
    </article>"""


def main():
    data = json.loads(REELS.read_text(encoding="utf-8")) if REELS.exists() else {"items": []}
    now = datetime.now(timezone.utc).astimezone(MSK)
    date_line = f"{now.day} {MONTHS_RU[now.month - 1]} {now.year}"

    chosen = pick(data["items"])
    share_url = urllib.parse.quote(SITE_URL, safe="")

    if chosen:
        body = "".join(card(i) for i in chosen)
    else:
        body = """<div class="empty">Копилка пока пуста. Увидел хороший рилс в Facebook —
        нажми «Поделиться» → «Скопировать ссылку» и пришли её нашему Telegram-боту.
        Утром здесь будет свежая дюжина. 🎬</div>"""

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reels дня — {date_line}</title>
<meta name="description" content="Ежедневная дюжина видео Reels. Обновляется каждый день в 08:00 по Москве.">
<style>
  :root {{ --bg:#0b1220; --card:#141d31; --txt:#e8edf7; --dim:#93a1bd; --pink:#ff2d78; --cyan:#4fc3f7; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--txt); font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; line-height:1.45; }}
  header {{ padding:28px 16px 18px; text-align:center; background:linear-gradient(180deg,#101a30,var(--bg)); border-bottom:1px solid #1e2a44; }}
  .badge {{ display:inline-block; background:var(--pink); color:#fff; font-weight:800; letter-spacing:.08em; padding:4px 14px; border-radius:6px; font-size:14px; }}
  h1 {{ font-size:clamp(24px,5vw,40px); margin:10px 0 4px; }} h1 .a {{ color:var(--pink); }}
  .date {{ color:var(--dim); font-size:15px; }}
  .share {{ margin-top:14px; display:flex; gap:10px; justify-content:center; flex-wrap:wrap; }}
  .share a {{ display:inline-block; padding:8px 16px; border-radius:999px; font-size:14px; font-weight:700;
    text-decoration:none; color:#fff; }}
  .fb {{ background:#1877f2; }} .tg {{ background:#2aabee; }} .wa {{ background:#25d366; }}
  main {{ max-width:1100px; margin:0 auto; padding:22px 14px 8px; display:grid;
    grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:18px; }}
  .card {{ background:var(--card); border:1px solid #1e2a44; border-radius:12px; overflow:hidden; }}
  .frame {{ position:relative; aspect-ratio:9/16; background:#000; }}
  .frame iframe {{ position:absolute; inset:0; width:100%; height:100%; border:0; }}
  .open {{ display:block; padding:10px 14px; color:var(--dim); font-size:13px; text-decoration:none; }}
  .empty {{ grid-column:1/-1; text-align:center; color:var(--dim); padding:60px 20px; font-size:16px; max-width:560px; margin:0 auto; }}
  footer {{ max-width:1100px; margin:0 auto; padding:14px 16px 34px; color:var(--dim); font-size:13px; text-align:center; }}
  .prov {{ font-style:italic; color:var(--cyan); margin-bottom:10px; }}
</style>
</head>
<body>
<header>
  <span class="badge">🎬 ДЮЖИНА ДНЯ</span>
  <h1>ВИДЕО <span class="a">REELS</span></h1>
  <div class="date">за {date_line} · 12 рилсов каждый день в 08:00 по Москве</div>
  <div class="share">
    <a class="fb" href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" rel="noopener">Поделиться в Facebook</a>
    <a class="tg" href="https://t.me/share/url?url={share_url}" target="_blank" rel="noopener">В Telegram</a>
    <a class="wa" href="https://wa.me/?text={share_url}" target="_blank" rel="noopener">В WhatsApp</a>
  </div>
</header>
<main>
{body}
</main>
<footer>
  <p class="prov">«Если уйдёшь оттуда, где тебя любят, придёшь туда, где тебя ненавидят» — сомалийская пословица</p>
  <p>Подборка обновляется автоматически. Все видео принадлежат их авторам и показываются
  официальным плеером Facebook.</p>
  <p style="margin-top:8px"><img src="https://abacus.jasoncameron.dev/hit/roman-reels/site?bg=0b1220&text=93a1bd" alt="" height="18"></p>
</footer>
</body>
</html>
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    REELS.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[ok] на странице {len(chosen)} рилсов, в копилке {len(data['items'])}")


if __name__ == "__main__":
    main()
