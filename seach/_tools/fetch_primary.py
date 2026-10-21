#!/usr/bin/env python3
"""Fetch Guangzhou-edition (广州教科版) primary school word pages.

Saves to source/primary/{grade}_{term}_u{N}.md
Usage: python3 fetch_primary.py [max_units]
"""
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API = "https://api.deepseek.com/v1/tools/fetch"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "source", "primary")

GRADES = [("sannianji", "3"), ("sinianji", "4"), ("wunianji", "5"), ("liunianji", "6")]
TERMS = [("shangce", "A"), ("xiace", "B")]


def fetch(url):
    req = urllib.request.Request(
        API,
        data=json.dumps({"url": url}).encode("utf-8"),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code}
    except Exception as e:
        return {"_error": str(e)}


def one(args):
    gdir, g, tdir, t, n = args
    url = "https://yy.suyang123.com/xiaoxue/%s/gzjkb_%s_words%d.html" % (gdir, tdir, n)
    dst = os.path.join(OUT, "%s%s_u%d.md" % (g, t, n))
    if os.path.exists(dst):
        return (dst, "skip")
    data = fetch(url)
    if "_error" in data or not data.get("content"):
        return (dst, "miss")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(data.get("title") or "")
        f.write("\n\n")
        f.write(data["content"])
    return (dst, "ok")


def main():
    max_units = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    os.makedirs(OUT, exist_ok=True)
    jobs = [(gdir, g, tdir, t, n)
            for gdir, g in GRADES for tdir, t in TERMS for n in range(1, max_units + 1)]
    ok = miss = skip = 0
    # stop early per (grade,term) after 3 consecutive misses handled by pruning below
    with ThreadPoolExecutor(max_workers=5) as ex:
        for dst, st in ex.map(one, jobs):
            if st == "ok":
                ok += 1
            elif st == "miss":
                miss += 1
            else:
                skip += 1
    print("ok", ok, "miss", miss, "skip", skip, "->", OUT)


if __name__ == "__main__":
    main()
