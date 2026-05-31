# /data/samples — Sample Pack v1

This folder contains the **demo corpus**: a tiny batch of PDFs + a machine-readable manifest.

## Contents
- `*.pdf` — 10 text-selectable PDFs (no scans)
- `metadata.csv` — one row per PDF (see schema below)

## File naming convention
`NN_surnameYYYY_shorttitle.pdf`  
- Example: `01_smith2021_transformer_summarisation.pdf`

## `metadata.csv` schema
paper_id,title,authors,year,doi,url_pdf,licence

### How to use it
- **paper_id**: matches the PDF file prefix (e.g., `01_smith2021_transformer.pdf`).
- **title**: full paper title.
- **authors**: `Surname I; Surname I; ...` (semi-colon separated).
- **year**: 4-digit year.
- **doi**: DOI string (or `n/a` if none).
- **url_pdf**: direct link to the PDF (OA, publisher, or library proxy).
- **licence**: `CC-BY 4.0`, `Publisher OA`, or `UOW library access (course use)`.

### Example rows
01,"Transformer-based Summarisation","Smith J; Patel R",2021,10.1145/1234567,https://arxiv.org/pdf/2101.00001.pdf,CC-BY 4.0
02,"Topic Modeling for Reviews","Lee K; Zhao Y",2020,10.1007/abcd1234,https://link.springer.com/content/pdf/10.1007/abcd1234.pdf,Publisher OA
03,"Neural Clustering Methods","Nguyen A; Carter T",2019,10.5555/9876543,https://arxiv.org/pdf/1905.00002.pdf,UOW library access (course use)

## Acceptance checklist
- [ ] All PDFs are text-selectable (copy/paste works).
- [ ] `metadata.csv` has no blanks in required fields.
- [ ] Each `paper_id` matches a file.
- [ ] Total folder size under ~100 MB.

## Out of scope (Phase 1)
- OCR for scanned PDFs
- Non-English content
- Automated crawling/scraping
