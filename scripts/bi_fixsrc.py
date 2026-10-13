#!/usr/bin/env python3
"""Burundi: check the `source` URL of every converted law; when the Assemblée's link is broken (404),
replace it by the corrected spelling that was actually downloaded (see bi_list.variants)."""
import glob
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_text as T  # noqa
from bi_list import variants  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ok(u):
    time.sleep(1)
    try:
        r = T._S.head(u, timeout=60, allow_redirects=True)
        return r.status_code == 200
    except Exception:  # noqa
        return False


for md in sorted(glob.glob(os.path.join(REPO, "*", "*.md")) + glob.glob(os.path.join(REPO, "lois", "*", "*.md"))):
    t = open(md, encoding="utf-8").read()
    if "\narchived_source:" in t.split("\n---\n", 1)[0]:
        continue
    m = re.search(r'^source: "([^"]+)"$', t, re.M)
    if not m or ok(m.group(1)):
        continue
    for v in variants(m.group(1))[1:]:
        if ok(v):
            t = t.replace('source: "%s"' % m.group(1), 'source: "%s"' % v, 1)
            open(md, "w", encoding="utf-8", newline="\n").write(t)
            print("fixed", md, v, flush=True)
            break
    else:
        print("BROKEN", md, m.group(1), flush=True)
