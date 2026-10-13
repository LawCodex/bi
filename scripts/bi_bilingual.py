#!/usr/bin/env python3
"""Burundi: some laws (and the Constitution) are printed in two columns, Kirundi and French side by side.
Whole-page OCR mixes the two languages; this script re-OCRs such documents column by column (left and
right half of each page image), keeps the French column and rewrites the Markdown body.
Bilingual documents are detected from Kirundi words in the converted files (run after bi_convert.py)."""
import glob
import os
import re
import subprocess
import sys
import tempfile
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "bi")
TESS = os.path.join(RAW, "tessdata")
KIRUNDI = re.compile(r"\b(ingingo|kandi|canke|ivyo|ukwo|uburundi|amategeko|ibwirizwa|abenegihugu)\b", re.I)
FR = {"le", "la", "les", "de", "des", "du", "et", "est", "en", "par", "une", "dans", "pour"}
RN = {"ya", "na", "ku", "mu", "kandi", "canke", "ivyo", "ingingo", "ko", "ni", "w", "y", "z"}


def ocr_half(pdf, page, side, td, w_pts, h_pts):
    """side 0 = left half, 1 = right half, 2 = whole page."""
    dpi = 300
    W, H = int(w_pts * dpi / 72), int(h_pts * dpi / 72)
    x = 0 if side != 1 else W // 2
    if side == 2:
        W = 2 * W
    base = os.path.join(td, "p%d_%d" % (page, side))
    subprocess.run(["pdftoppm", "-r", str(dpi), "-gray", "-png", "-f", str(page), "-l", str(page), "-singlefile",
                    "-x", str(x), "-y", "0", "-W", str(W // 2 + (W % 2)), "-H", str(H), pdf, base], capture_output=True)
    env = dict(os.environ, TESSDATA_PREFIX=TESS)
    r = subprocess.run(["tesseract", base + ".png", "-", "-l", "fra", "--psm", "6"], capture_output=True, env=env)
    os.remove(base + ".png")
    return r.stdout.decode("utf-8", "replace")


def lang_score(t, words):
    toks = re.findall(r"[a-zàâçéèêëîïôûù]+", t.lower())
    return sum(1 for x in toks if x in words)


def work(args):
    md, url = args
    pdf = os.path.join(RAW, "bil", os.path.basename(md)[:-3] + ".pdf")
    from bi_list import variants
    if not any(T.fetch(u, pdf, delay=2, check_pdf=True, tries=2) for u in variants(url)):
        return md, "download failed"
    info = subprocess.run(["pdfinfo", pdf], capture_output=True).stdout.decode("latin-1")
    n = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    w, h = map(float, re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info).groups())
    pages = []
    with tempfile.TemporaryDirectory(dir=RAW) as td:
        for p in range(1, n + 1):
            L = ocr_half(pdf, p, 0, td, w, h)
            R = ocr_half(pdf, p, 1, td, w, h)
            # French column = the one with more French function words (single-column pages: keep whole text)
            fl, fr_ = lang_score(L, FR), lang_score(R, FR)
            rl, rr = lang_score(L, RN), lang_score(R, RN)
            if (fl > rl) == (fr_ > rr):  # both halves look the same language: not a two-column page
                pages.append(ocr_half(pdf, p, 2, td, w, h) if fl > rl else "")
            else:
                pages.append(L if fl - rl > fr_ - rr else R)
    return md, pages


def main():
    targets = []
    for md in sorted(glob.glob(os.path.join(REPO, "lois", "*", "*.md")) + glob.glob(os.path.join(REPO, "constitution", "*.md"))):
        t = open(md, encoding="utf-8").read()
        if len(KIRUNDI.findall(t)) >= 15:
            fm = t.split("\n---\n", 1)[0]
            m = re.search(r'^archived_source: "([^"]+)"', fm, re.M) or re.search(r'^source: "([^"]+)"', fm, re.M)
            targets.append((md, m.group(1)))
    print(len(targets), "bilingual documents", flush=True)
    with Pool(int(os.environ.get("LC_JOBS", "6"))) as pool:
        for md, pages in pool.imap_unordered(work, targets):
            if isinstance(pages, str):
                print("FAIL", md, pages, flush=True)
                continue
            txt = "\n".join(pages)
            if len(txt) < 300 or T.text_quality(txt) < 0.75:
                print("LOWQ", md, flush=True)
                continue
            t = open(md, encoding="utf-8").read()
            fm, rest = t.split("\n---\n", 1)
            title = re.search(r"^# (.*)$", rest, re.M).group(1)
            fm = re.sub(r'^note: ".*"$', 'note: "Bilingual (Kirundi/French) print: French column only, text obtained by OCR (tesseract, French) from the scanned PDF published by the Assemblée nationale; may contain recognition errors."', fm, flags=re.M)
            body = T.structure(T.clean_pages(pages), "fr")
            with open(md, "w", encoding="utf-8", newline="\n") as f:
                f.write(fm + "\n---\n\n# " + title + "\n\n" + "\n".join(body).strip() + "\n")
            print("ok", md, flush=True)


if __name__ == "__main__":
    main()
