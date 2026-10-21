#!/usr/bin/env python3
"""DeepSeek Search / Fetch helper.

Usage:
  python ds.py search "query" [out.json] [count]
  python ds.py fetch "url" [out.md]
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://api.deepseek.com"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")


def _post(path, payload):
    if not KEY:
        sys.exit("DEEPSEEK_API_KEY not set")
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "ignore")[:500]))


def search(query, count=10, need_content=True):
    return _post(
        "/v1/tools/search",
        {"query": query, "count": count, "need_content": need_content},
    )


def fetch(url):
    return _post("/v1/tools/fetch", {"url": url})


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "search":
        query = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 else "search.json"
        count = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        data = search(query, count=count)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        for it in data.get("results", []):
            print("%-6s %-45s %s" % (
                round(it.get("rerank_score") or 0, 2),
                (it.get("title") or "")[:45],
                len(it.get("content") or ""),
            ))
        print("saved:", out, "results:", len(data.get("results", [])))
    elif cmd == "fetch":
        url = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 else "page.md"
        data = fetch(url)
        with open(out, "w", encoding="utf-8") as f:
            f.write(data.get("title") or "")
            f.write("\n\n")
            f.write(data.get("content") or "")
        print("saved:", out, "title:", data.get("title"), "len:", len(data.get("content") or ""))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
