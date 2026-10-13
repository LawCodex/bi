#!/usr/bin/env python3
"""Burundi: convert the laws downloaded by bi_list.py (text from bi_ocr.py) to Markdown (French)."""
import hashlib
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "bi")
RETRIEVED = os.environ.get("LC_RETRIEVED", "2026-10-13")
MONTHS = "janvier|f[ée]vrier|fevr|mars|avril|mai|juin|juillet|ao[uû]t|septembre|sept|octobre|novembre|d[ée]cembre"


def year_of(title, post_title):
    m = re.search(r"promulgu[ée]+s?\s+(?:en\s+)?((?:19|20)\d\d)", post_title, re.I)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{1,2}(?:er)?\s+(?:%s)\.?\s+((?:19|20)\d\d))\b" % MONTHS, title, re.I)
    if m:
        return m.group(2)
    m = re.search(r"\b((?:19|20)\d\d)\b", title) or re.search(r"\b((?:19|20)\d\d)\b", post_title)
    return m.group(1) if m else None


def ident_of(title):
    m = re.match(r"^((?:D[ée]cret-)?Loi(?: organique)?\s+n\s*[°o]?\s*\d+\s*/\s*\d+(?:\s+du\s+\d{1,2}(?:er)?\s+\w+\.?\s+\d{4})?)", title, re.I)
    return m.group(1) if m else None


def main():
    items = json.load(open(os.path.join(RAW, "laws.json")))
    stats = Counter()
    seen = set()
    for it in items:
        title = it["title"].strip()
        if re.search(r"R[èe]glement Int[ée]rieur|questeurs", title, re.I) or it["url"].endswith(("RI20_25.pdf", "RI2018.pdf")):
            continue
        pdf = os.path.join(RAW, "pdf", it["file"])
        if not os.path.exists(pdf) or not T.pdf_ok(pdf):
            stats["missing"] += 1
            continue
        h = hashlib.md5(open(pdf, "rb").read()).hexdigest()
        if h in seen:
            stats["duplicate"] += 1
            continue
        seen.add(h)
        if not os.path.exists(pdf + ".text.json"):
            stats["not-ocred"] += 1
            continue
        pages, ocr = T.pdf_text(pdf, "fra")
        txt = "\n".join(pages)
        if len(txt.strip()) < 300 or T.text_quality(txt) < 0.75:
            stats["low-quality"] += 1
            print("LOWQ", round(T.text_quality(txt), 2), title[:80])
            continue
        is_const = title.lower().startswith("constitution")
        year = "2018" if is_const else year_of(title, it["post_title"])
        lines = T.clean_pages(pages)
        body = T.structure(lines, "fr")
        typ = "constitution" if is_const else ("organic_law" if re.match(r"^Loi organique", title, re.I) else
                                                 "decree_law" if re.match(r"^D[ée]cret", title, re.I) else "law")
        ident = ident_of(title)
        meta = {"title": title, "identifier": ident, "type": typ, "jurisdiction": "bi", "language": "fr",
                "year": int(year) if year else None, "status": "in_force" if is_const else "unknown",
                "source": it.get("fetched_url") or it["url"], "source_page": it["post"], "retrieved": RETRIEVED}
        if it.get("archived_url"):
            meta["archived_source"] = it["archived_url"]
        if ocr:
            meta["note"] = "Text obtained by OCR (tesseract, French) from the scanned PDF published by the Assemblée nationale; may contain recognition errors."
        if is_const:
            path = os.path.join(REPO, "constitution", "constitution-2018.md")
        else:
            base = T.slug(ident or title, 90)
            d = os.path.join(REPO, "lois", year or "undated")
            path = os.path.join(d, base + ".md")
            if path in seen:
                path = os.path.join(d, base + "-" + h[:6] + ".md")
        seen.add(path)
        T.write_md(path, meta, title, body)
        stats[typ] += 1
    print(dict(stats))


if __name__ == "__main__":
    main()
