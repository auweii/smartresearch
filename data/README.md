# /data

This directory holds **small, legally downloadable sample corpora** used for development and demo.
It is the single place for example PDFs and their manifest so no one has to guess what's in the batch.

## Structure

/data
└── /samples
    ├── 01_surnameYYYY_shorttitle.pdf
    ├── 02_surnameYYYY_shorttitle.pdf
    ├── ...
    └── metadata.csv

## Rules (Phase 1)
- English, **text-selectable PDFs only** (no scanned images / no OCR).
- No personal/sensitive data. Use **open-access** sources where possible.
- Every PDF must have a row in `metadata.csv` (see `/data/samples/README.md`).

## Why this exists
- **Reproducibility:** pipeline/scripts can read one manifest (CSV) for the whole batch.
- **Traceability:** each file has a source and licence in the CSV.
- **Speed:** quick search/filter by DOI, year, authors without opening PDFs.
- - **Single source of truth:** all demo/sample files must be stored here; no duplicates elsewhere.
