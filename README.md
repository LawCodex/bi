# Burundi (BI) — legislation as Markdown

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as plain Markdown in git.

Legislation of the Republic of Burundi, in **French**, from the official website of the **Assemblée nationale du
Burundi** (assemblee.bi):

* the **Constitution de la République du Burundi** of 7 June 2018 ("Textes de référence");
* the **laws promulgated** from 2003 to 2026 (*Lois promulguées*, one page per year), including organic laws,
  codes (penal code, electoral code, …), finance laws and laws ratifying international agreements.

Retrieved 2026-10-13.

<!-- COUNTS -->
| Directory | Files |
|---|---|
| `constitution/` | 1 |
| `lois/` | 494 |
| **Total** | **495** |
<!-- /COUNTS -->

## Structure

```
constitution/constitution-2018.md
lois/<year>/<slug>.md            year = year of promulgation (from the Assemblée's yearly list)
```

File names are slugs of the law number (e.g. `loi-n-1-05-du-16-mars-2023.md`). Front matter: `title` is the
title given in the Assemblée's list, `identifier` the law number and date, `source` the PDF, `source_page` the
yearly list. `status` is `unknown` (the source does not indicate amendments or repeal).

## Text and OCR

**All PDFs published by the Assemblée nationale are scans without a text layer.** Their text was produced by OCR
(tesseract 5, French `tessdata_fast` model, 300 dpi); every file carries a `note` saying so. OCR output was kept
only when it passed a plausibility check (share of well-formed words); it still contains recognition errors
(stamps, signatures, tables and handwritten dates are typically garbled). Headings (`TITRE`, `CHAPITRE`,
`Section`, `Article N`) are recognised from the OCR text.

The Constitution and about 25 recent laws are printed in two columns, **Kirundi and French side by side**. For
these, each page image was split into its two halves, both were OCRed, and only the **French column** is kept
(no Kirundi OCR model is available); their `note` says so. Kirundi texts are therefore not included.

## Sources

| Source | URL | Used for |
|---|---|---|
| Assemblée nationale du Burundi — Lois promulguées | https://assemblee.bi/?cat=7 (REST: `/?rest_route=/wp/v2/posts&categories=7`) | laws |
| Assemblée nationale du Burundi — Textes de référence | https://assemblee.bi/2024/03/06/textes-de-reference/ | Constitution |

## Not covered / known gaps

* Laws before 2003, and laws missing from the Assemblée's yearly lists, are not included.
* Some links on the site are broken (HTTP 404); alternative spellings of the file names and Internet Archive copies
  of the official files (`archived_source` in the front matter) were tried; 17 laws remain missing. One OCR result
  failed the quality check and was dropped.
* Decrees and ordinances (published by the Presidency, presidence.gov.bi, and in the *Bulletin officiel du
  Burundi*, which is not online) are not included. The Assembly's internal rules of procedure are excluded.
* No consolidation: laws are as promulgated; amending laws are separate files.

## Copyright

Burundian laws are official public texts. The Markdown conversion (OCR) is provided as is, for information; the
authoritative text is the one promulgated and published in the *Bulletin officiel du Burundi*.

## Regenerate

```
python3 -m pip install -r scripts/requirements.txt   # plus poppler and tesseract
python3 scripts/bi_list.py --download   # list + PDFs into ../_raw/bi
python3 scripts/bi_ocr.py               # OCR (French model in ../_raw/bi/tessdata, from tesseract-ocr/tessdata_fast)
python3 scripts/bi_convert.py
python3 scripts/bi_bilingual.py         # re-OCR of Kirundi/French two-column prints, French column
python3 scripts/bi_fixsrc.py            # record the working URL of links that are broken on the site
python3 scripts/bi_readme.py
```
