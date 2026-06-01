# SmartResearch — Frontend Source

The `src/` directory contains the core source files for the SmartResearch frontend.

The frontend is built with React and Vite, styled with Tailwind CSS, and connected to the FastAPI backend through REST API requests. It provides the user-facing workflows for PDF upload, paper review, metadata inspection, summary generation, keyword search, semantic search, hybrid search, clustering, recommendations, deletion, and PDF report export.

---

## Directory Structure

```text
src/
├── components/
│   ├── README.md        # Reusable UI-component documentation
│   ├── Navbar.jsx       # Global route navigation
│   ├── Dropzone.jsx     # Multi-file PDF upload and preview
│   ├── Card.jsx         # Reusable content wrapper
│   ├── Button.jsx       # Reusable button variants
│   ├── Table.jsx        # Generic table utility
│   └── Modal.jsx        # Accessible modal utility
├── pages/
│   ├── README.md        # Page-level workflow documentation
│   ├── UploadPage.jsx   # PDF upload entry point
│   ├── AllPapersPage.jsx # Paper browsing, search, metadata, and deletion
│   ├── FullSummary.jsx  # Detailed paper view and summary generation
│   ├── ClusterPage.jsx  # Cluster exploration and grouped-paper display
│   └── ExportPage.jsx   # Configurable PDF report export
├── api.js               # Shared Axios API helpers
├── App.jsx              # Root router and shared layout
├── main.jsx             # React entry point and BrowserRouter setup
├── index.css            # Tailwind directives and shared custom styles
└── README.md            # Frontend source documentation
```

---

## Technology Stack

| Layer                | Description                                                             |
| -------------------- | ----------------------------------------------------------------------- |
| **React**            | Provides the component-based frontend interface.                        |
| **Vite**             | Provides the frontend development server and production build pipeline. |
| **Tailwind CSS**     | Provides utility-first styling and the custom bronze visual palette.    |
| **React Router DOM** | Handles client-side navigation between application routes.              |
| **Axios**            | Handles communication with FastAPI backend endpoints.                   |
| **React PDF Viewer** | Displays completed PDF uploads in the frontend preview modal.           |

---

## Source Architecture

| Layer             | Purpose                                                                                                         |
| ----------------- | --------------------------------------------------------------------------------------------------------------- |
| **Components**    | Provides reusable navigation, upload, layout, table, button, and modal utilities.                               |
| **Pages**         | Implements route-level workflows for upload, paper review, detailed summary generation, clustering, and export. |
| **API Module**    | Centralises reusable Axios requests and backend configuration.                                                  |
| **Router**        | Maps URL paths to page components and provides the shared navigation layout.                                    |
| **Styling Layer** | Defines Tailwind directives, bronze-themed UI utilities, shared button styles, and global layout behaviour.     |

---

## API Configuration

The shared API module is defined in `api.js`.

It uses the `VITE_API_URL` environment variable when available:

```text
VITE_API_URL
```

When the variable is not configured, the frontend falls back to:

```text
http://127.0.0.1:8000
```

The shared Axios instance applies the `/api` prefix automatically.

Example:

```javascript
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
});
```

---

## Shared API Helpers

| Helper             | Backend Endpoint            | Purpose                                           |
| ------------------ | --------------------------- | ------------------------------------------------- |
| `uploadPaper()`    | `POST /api/upload`          | Uploads a PDF for backend processing.             |
| `getPapers()`      | `GET /api/docs`             | Retrieves stored document records.                |
| `deletePaper()`    | `DELETE /api/docs/{id}`     | Deletes a stored document and related local data. |
| `getPaperText()`   | `GET /api/text/{id}`        | Retrieves extracted document text.                |
| `getPaperMeta()`   | `GET /api/meta/{id}`        | Retrieves stored and enriched metadata.           |
| `getClusters()`    | `GET /api/clustered`        | Retrieves generated document clusters.            |
| `searchPapers()`   | `POST /api/search`          | Performs TF-IDF keyword search.                   |
| `keywordSearch()`  | `POST /api/search`          | Performs TF-IDF keyword search.                   |
| `semanticSearch()` | `POST /api/semantic_search` | Performs transformer-based semantic search.       |
| `hybridSearch()`   | `POST /api/hybrid_search`   | Combines keyword and semantic-search scores.      |
| `exportPDF()`      | `POST /api/export`          | Generates a downloadable PDF report.              |

Some page-specific requests are currently issued directly with Axios where specialised behaviour is required.

---

## Route Map

| Route         | Component       | Purpose                                                                        |
| ------------- | --------------- | ------------------------------------------------------------------------------ |
| `/`           | Redirect        | Redirects users to `/upload`.                                                  |
| `/upload`     | `UploadPage`    | Uploads, tracks, and previews PDF documents.                                   |
| `/papers`     | `AllPapersPage` | Browses, searches, inspects, and deletes stored papers.                        |
| `/papers/:id` | `FullSummary`   | Displays detailed metadata, generates summaries, and shows recommended papers. |
| `/cluster`    | `ClusterPage`   | Displays clustered research themes and grouped papers.                         |
| `/export`     | `ExportPage`    | Configures and downloads PDF reports.                                          |

---

## Page Interaction Flow

### Upload Page

The Upload page:

1. Retrieves existing stored documents.
2. Accepts one or more PDF files through the `Dropzone` component.
3. Sends each selected file to `POST /api/upload`.
4. Displays uploading, processing, completed, or failed states.
5. Allows users to preview successfully uploaded PDFs locally.
6. Links users to the All Papers view.

---

### All Papers Page

The All Papers page:

1. Retrieves stored records from `GET /api/docs`.
2. Retrieves enriched metadata from `GET /api/meta/{id}`.
3. Displays uploaded papers in a searchable table.
4. Supports keyword, semantic, and hybrid search modes.
5. Displays relevance scores for ranked results.
6. Allows users to inspect paper details.
7. Allows users to delete individual papers or clear the stored list.

---

### Full Summary Page

The Full Summary page:

1. Retrieves stored metadata from `GET /api/meta/{id}`.
2. Checks local GPU availability through `GET /api/system/gpu`.
3. Generates short, medium, or long abstractive summaries through `POST /api/summarize/{id}`.
4. Allows generated summaries to replace the stored summary through `PATCH /api/meta/{id}/summary`.
5. Retrieves recommended papers through `GET /api/external_recs/{id}`.
6. Displays a CPU-performance notice when GPU acceleration is unavailable.

---

### Cluster Page

The Cluster page:

1. Retrieves generated clusters from `GET /api/clustered`.
2. Retrieves stored document records from `GET /api/docs`.
3. Maps cluster paper IDs to stored papers.
4. Extracts and displays cluster keywords.
5. Supports cluster filtering and sorting.
6. Displays grouped papers in cluster-detail views.

---

### Export Page

The Export page:

1. Allows users to configure report contents.
2. Supports paper lists, cluster tables, grouped papers, summaries, keywords, charts, and optional recommendations.
3. Sends the export request to `POST /api/export`.
4. Downloads the generated PDF response through the browser.

PDF is the supported final export format. CSV and JSON options remain disabled in the current frontend.

---

## Styling System

The frontend uses a custom bronze-themed Tailwind palette defined in `tailwind.config.cjs`.

Shared styles in `index.css` include:

* Global page background and typography rules
* Bronze-themed checkbox and radio-button accents
* Primary, secondary, and ghost button utilities
* Shared field-focus behaviour
* Modal-backdrop styling

---

## Development Workflow

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The development server runs at the default Vite address:

```text
http://localhost:5173
```

Start the FastAPI backend separately so the frontend can communicate with the API.

---

## Production Build

Generate a production build:

```bash
npm run build
```

Preview the generated build locally:

```bash
npm run preview
```

---

## Implementation Notes

* The frontend uses local React state and props rather than a global state-management library.
* `main.jsx` wraps the application in `BrowserRouter`.
* `App.jsx` provides the shared navigation bar and declares the frontend routes.
* `Dropzone.jsx` provides PDF upload tracking and completed-upload previews.
* Some API calls use the shared `api.js` helpers, while some page-specific calls currently use direct Axios requests.
* Future refactoring should centralise remaining direct Axios requests in `api.js` for consistency.
