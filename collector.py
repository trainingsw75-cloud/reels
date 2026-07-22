# -*- coding: utf-8 -*-
"""Сборщик ссылок на рилсы из Telegram.

Роман кидает ссылки на Facebook-рилсы боту, робот раз в два часа забирает их
через getUpdates и складывает в reels.json. Чужие сообщения игнорируются.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REELS = ROOT / "reels.json"
STATE = ROOT / "state.json"

OWNER_ID = 6357249473  # Telegram Романа
URL_RE = re.compile(r"https?://[^\s]*(?:facebook\.com|fb\.watch)/[^\s]+", re.IGNORECASE)


UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def clean_url(url):
    """Обрезает хвосты (?rdid=…, ?mibextid=…) у ссылок на рилсы."""
    parts = urllib.parse.urlsplit(url)
    if "/reel/" in parts.path or "/videos/" in parts.path:
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return url


def resolve_share_link(url):
    """Короткие ссылки /share/r/… плеер Facebook не понимает —
    разворачиваем их в полные /reel/…"""
    if "/share/" not in url and "fb.watch" not in url:
        return clean_url(url)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            final = r.geturl()
    except Exception as e:
        print(f"[warn] не развернул {url}: {e}")
        return url
    if "login" in final:  # стена логина: целевой адрес лежит в параметре next=
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(final).query)
        final = qs.get("next", [final])[0]
    return clean_url(final)


def api(token, method, **params):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
        return json.loads(r.read())


def load(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def main():
    token = os.environ.get("REELS_BOT_TOKEN", "").strip().strip("﻿")
    if not token:
        print("[skip] REELS_BOT_TOKEN не настроен — пропускаю сбор")
        return

    reels = load(REELS, {"items": []})
    state = load(STATE, {"offset": 0})
    known = {i["url"] for i in reels["items"]}

    resp = api(token, "getUpdates", offset=state["offset"] + 1, timeout=0)
    if not resp.get("ok"):
        sys.exit(f"getUpdates failed: {resp}")

    added_total = 0
    for upd in resp["result"]:
        state["offset"] = max(state["offset"], upd["update_id"])
        msg = upd.get("message") or {}
        frm = (msg.get("from") or {}).get("id")
        if frm != OWNER_ID:
            continue
        text = (msg.get("text") or "") + " " + (msg.get("caption") or "")
        urls = [resolve_share_link(u.rstrip(".,;)») ")) for u in URL_RE.findall(text)]
        fresh = [u for u in urls if u not in known]
        for u in fresh:
            known.add(u)
            reels["items"].append({
                "url": u,
                "added": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "shown": 0,
            })
        added_total += len(fresh)
        if fresh:
            api(token, "sendMessage", chat_id=frm,
                text=f"🎬 Принял {len(fresh)} шт. Всего в копилке: {len(reels['items'])}. "
                     f"Свежая дюжина выйдет завтра в 08:00.")
        elif text.strip() and not urls:
            api(token, "sendMessage", chat_id=frm,
                text="Пришли мне ссылку на рилс из Facebook: под видео «Поделиться» → "
                     "«Скопировать ссылку», и вставь её сюда.")

    REELS.write_text(json.dumps(reels, ensure_ascii=False, indent=1), encoding="utf-8")
    STATE.write_text(json.dumps(state), encoding="utf-8")
    print(f"[ok] новых ссылок: {added_total}, всего: {len(reels['items'])}")


if __name__ == "__main__":
    main()
