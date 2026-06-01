# SmartResearch — Page Views

This directory contains the top-level page components for the SmartResearch frontend.

Each page represents a route-level workflow and coordinates the required UI components, local state, and backend API requests. Together, the pages provide the user-facing interface for PDF upload, paper review, summary generation, search, clustering, recommendations, deletion, and PDF report export.

---

## Directory Overview

```text
src/pages/
├── UploadPage.jsx     # PDF upload entry point and completed-upload preview
├── AllPapersPage.jsx  # Paper browsing, metadata display, search, and deletion
├── FullSummary.jsx    # Detailed metadata, summary generation, and recommendations
├── ClusterPage.jsx    # Cluster exploration and grouped-paper display
├── ExportPage.jsx     # Configurable PDF report export
└── README.md          # Page-level workflow documentation
```

---

## Page Responsibilities

| Page                | Route         | Description                                                                                                                                                                                                   |
| ------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UploadPage.jsx`    | `/upload`     | Provides the PDF upload entry point. Loads existing stored documents, renders the `Dropzone` component, tracks selected files, and links users to the All Papers view.                                        |
| `AllPapersPage.jsx` | `/papers`     | Retrieves stored papers and enriched metadata, displays the paper table, supports keyword, semantic, and hybrid search, shows ranked results, opens metadata details, and allows individual or bulk deletion. |
| `FullSummary.jsx`   | `/papers/:id` | Displays detailed metadata, checks GPU availability, generates short, medium, or long abstractive summaries, allows summary replacement, and retrieves recommended papers.                                    |
| `ClusterPage.jsx`   | `/cluster`    | Retrieves cluster data and stored document records, maps paper IDs to documents, extracts cluster keywords, supports filtering and sorting, and displays grouped papers.                                      |
| `ExportPage.jsx`    | `/export`     | Allows users to configure report contents and download a generated PDF report from the backend.                                                                                                               |

---

## Route Map

Routes are declared in `App.jsx`.

| Route         | Component       | Purpose                                                      |
| ------------- | --------------- | ------------------------------------------------------------ |
| `/`           | Redirect        | Redirects users to `/upload`.                                |
| `/upload`     | `UploadPage`    | Uploads and previews PDF documents.                          |
| `/papers`     | `AllPapersPage` | Browses, searches, inspects, and deletes stored papers.      |
| `/papers/:id` | `FullSummary`   | Displays detailed paper information and generates summaries. |
| `/cluster`    | `ClusterPage`   | Displays research-paper clusters and grouped papers.         |
| `/export`     | `ExportPage`    | Configures and downloads PDF reports.                        |

---

## Workflow Details

### Upload Page

`UploadPage.jsx`:

* Loads stored documents through `GET /api/docs`
* Renders `Dropzone`
* Supports multiple PDF uploads
* Displays stored-paper status
* Links users to `/papers`

The upload workflow itself is handled by `Dropzone.jsx`, which sends each selected file to:

```text
POST /api/upload
```

---

### All Papers Page

`AllPapersPage.jsx`:

* Retrieves stored document records through `GET /api/docs`
* Retrieves enriched metadata through `GET /api/meta/{id}`
* Displays titles, filenames, summaries, authors, publication years, and relevance scores
* Supports keyword search through `POST /api/search`
* Supports semantic search through `POST /api/semantic_search`
* Supports hybrid search through `POST /api/hybrid_search`
* Opens detailed paper metadata
* Deletes individual papers through `DELETE /api/docs/{id}`
* Supports bulk deletion of displayed papers

The page renders a specialised table directly because its row behaviour, metadata enrichment, search states, and delete controls are page-specific.

---

### Full Summary Page

`FullSummary.jsx`:

* Retrieves stored metadata through `GET /api/meta/{id}`
* Checks GPU availability through `GET /api/system/gpu`
* Generates abstractive summaries through `POST /api/summarize/{id}`
* Supports `short`, `medium`, and `long` summary targets
* Replaces the stored summary through `PATCH /api/meta/{id}/summary`
* Retrieves recommended papers through `GET /api/external_recs/{id}`
* Displays a CPU-performance notice when GPU acceleration is unavailable

---

### Cluster Page

`ClusterPage.jsx`:

* Retrieves cluster data through `GET /api/clustered`
* Retrieves stored papers through `GET /api/docs`
* Maps cluster paper IDs to stored document records
* Extracts keyword labels from cluster descriptions
* Supports cluster filtering and sorting
* Displays grouped-paper details in a modal

---

### Export Page

`ExportPage.jsx`:

* Allows users to select report sections
* Supports paper lists, cluster tables, grouped papers, summaries, keywords, charts, and optional recommendations
* Sends export requests to `POST /api/export`
* Downloads the returned report through the browser

PDF is the supported final export format.

CSV and JSON controls remain visible as disabled future options.

---

## Architecture Notes

* Each page is implemented as a React functional component.
* Page state is managed locally with React hooks.
* Routes are declared in `App.jsx` through `react-router-dom`.
* Shared UI components are imported from `../components/`.
* Shared API helpers are imported from `../api.js` where available.
* Some specialised page requests currently use direct Axios calls.
* The frontend uses the shared bronze-accent Tailwind design system.
* No global state-management library is used.

---

## Example Route Integration

```jsx
import { Routes, Route, Navigate } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import AllPapersPage from "./pages/AllPapersPage";
import FullSummary from "./pages/FullSummary";
import ClusterPage from "./pages/ClusterPage";
import ExportPage from "./pages/ExportPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/upload" replace />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/papers" element={<AllPapersPage />} />
      <Route path="/papers/:id" element={<FullSummary />} />
      <Route path="/cluster" element={<ClusterPage />} />
      <Route path="/export" element={<ExportPage />} />
    </Routes>
  );
}
```
