# /data/samples — Sample Pack v1

This folder contains the **demo corpus**: a tiny batch of PDFs + a machine-readable manifest.

## Contents
- `*.pdf` — 10 text-selectable PDFs (no scans)
- `metadata.csv` — one row per PDF (minimum columns below)

## File naming
`NN_surnameYYYY_shorttitle.pdf`  
- Example: `01_smith2021_transformer_summarisation.pdf`

## `metadata.csv` (minimum schema)
paper_id,title,authors,year,doi,url_pdf,licence

## Acceptance checklist
- [ ] All PDFs are text-selectable (copy/paste works).
- [ ] `metadata.csv` has no blanks in required fields.
- [ ] Each `paper_id` matches a file.
- [ ] Total folder size under ~100 MB.

## Out of scope (Phase 1)
- OCR for scanned PDFs
- Non-English content
- Automated crawling/scraping
