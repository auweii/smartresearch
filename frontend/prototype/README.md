# SmartResearch — Static Prototype Suite

This folder contains the finalised **HTML prototype version** of SmartResearch.  
It demonstrates the complete end-to-end workflow — from **uploading PDFs** to **clustering, exporting, and merging reports** — using static pages and local storage.  
This version predates the React + FastAPI build and was used to validate the core UX flow before full integration.

---

## Overview

| Page | Purpose |
|------|----------|
| `upload.html` | Drag-and-drop PDF uploader with progress simulation and file list. |
| `papers.html` | Displays all uploaded papers and their summaries (local only). |
| `cluster.html` | Groups uploaded papers into thematic clusters using mock data. |
| `export.html` | Exports data as JSON or generates a printable report view. |
| `report.html` | Creates a formatted report of clusters and summaries for printing or PDF saving. |
| `merge.html` | Allows merging of two exported datasets and previews differences. |
| `style.css` | Unified styling — color palette, layout grid, cards, modals, and typography. |
| `app.js` | Core logic managing papers, clusters, and summaries via `localStorage`. |

---

## How It Works

All data operations run **entirely in-browser** using `localStorage`.  
There is **no backend connection** — instead, simulated functions handle uploads, clustering, and exports.

- `getPapers()`, `setPapers()` → store/retrieve document info  
- `getSummaries()`, `setSummaries()` → manage summaries  
- `getClusters()`, `setClusters()` → handle topic groups  
- `fakeCluster()` → generates mock clusters for demo purposes  
- `buildExport()` → bundles all stored data for export or reporting  

---

## Prototype Flow

1. **Upload** – Add sample PDFs on `upload.html` (simulated progress).  
2. **All Papers** – Review uploaded documents and summaries.  
3. **Cluster** – Automatically generate topic clusters and view details in modals.  
4. **Export** – Download JSON or open printable report view.  
5. **Merge** – Combine exports from different sessions.  

---

## Purpose

- Demonstrate the **intended user experience** before API integration.  
- Validate **navigation flow and component hierarchy**.  
- Serve as a **UI reference** for React migration and backend mapping.  

---

## How to Run

You can open any HTML file directly in your browser or serve locally for full routing support:

```bash
cd frontend/prototype
python -m http.server 5500
