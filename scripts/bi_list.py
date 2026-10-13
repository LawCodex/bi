#!/usr/bin/env python3
"""Burundi: list the laws published by the Assemblée nationale du Burundi ("Lois promulguées",
WordPress REST API of assemblee.bi) plus the reference texts (Constitution), download the PDFs
to ../../_raw/bi/pdf and write ../../_raw/bi/laws.json."""
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "bi")
API = "https://assemblee.bi/?rest_route=/wp/v2/posts&categories=%d&per_page=100"
CATS = {7: "lois-promulguees", 5: "telechargements"}


def quote(u):
    p = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(urllib.parse.unquote(p.path)), p.query, ""))


def variants(u):
    """Some links on the site are broken (typos, spaces vs dashes): candidate corrected URLs."""
    v = [u]
    u2 = u.replace("://assemblee.b/", "://assemblee.bi/").replace("/website/wp-content/", "/wp-content/")
    v.append(u2)
    v.append(u2.replace("%20", "-"))
    v.append(u2.replace("%20", "_"))
    v.append(re.sub(r"(\.pdf)$", r"-1\1", u2.replace("%20", "-")))
    out = []
    for x in v:
        if x not in out:
            out.append(x)
    return out


def main():
    items = []
    for cat, name in CATS.items():
        p = os.path.join(RAW, "cat%d.json" % cat)
        T.fetch(API % cat, p, delay=2)
        for post in json.load(open(p)):
            ptitle = html.unescape(post["title"]["rendered"])
            for href, txt in re.findall(r'<a[^>]*href="([^"]+\.pdf)"[^>]*>(.*?)</a>', post["content"]["rendered"], re.S | re.I):
                txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", txt))).strip().rstrip(" ;")
                items.append({"cat": name, "post": post["link"], "post_title": ptitle, "url": quote(html.unescape(href)), "title": txt})
    seen = set()
    out = []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        it["file"] = hashlib.sha1(it["url"].encode()).hexdigest()[:16] + ".pdf"
        out.append(it)
    json.dump(out, open(os.path.join(RAW, "laws.json"), "w"), indent=1, ensure_ascii=False)
    print(len(out), "documents")
    if "--download" in sys.argv:
        for it in out:
            r = None
            for k, u in enumerate(variants(it["url"])):
                r = T.fetch(u, os.path.join(RAW, "pdf", it["file"]), delay=2, check_pdf=True, tries=3 if k == 0 else 1)
                if r:
                    if u != it["url"]:
                        it["fetched_url"] = u
                    break
            print("ok" if r else "FAIL", it["url"], flush=True)
        json.dump(out, open(os.path.join(RAW, "laws.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
