#!/usr/bin/env python3
"""Extract text from the downloaded PDFs (../../_raw/bi/pdf), running tesseract OCR (French) on
scanned pages, 4 documents in parallel. Results are cached next to each PDF (<pdf>.text.json).
French model: tessdata_fast fra.traineddata in ../../_raw/bi/tessdata (env LC_TESSDATA)."""
import glob
import os
import sys
import tempfile
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "bi")
LANG = os.environ.get("LC_OCR_LANG", "fra")


def work(path):
    if os.path.exists(path + ".text.json"):
        return path, "cached"
    if not T.pdf_ok(path):
        return path, "bad pdf"
    with tempfile.TemporaryDirectory(dir=RAW) as td:
        pages, used = T.pdf_text(path, LANG, tmpdir=td)
    return path, "ocr" if used else "text"


if __name__ == "__main__":
    os.environ.setdefault("LC_TESSDATA", os.path.join(RAW, "tessdata"))
    files = sorted(glob.glob(os.path.join(RAW, "pdf", "*.pdf")))
    with Pool(int(os.environ.get("LC_JOBS", "4"))) as p:
        for path, st in p.imap_unordered(work, files):
            print(st, os.path.basename(path), flush=True)
