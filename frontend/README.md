# SmartResearch — Frontend

The **SmartResearch Frontend** provides the user interface for interacting with the FastAPI backend.

It is built with **React**, **Vite**, and **Tailwind CSS**, with Axios-based API communication and route-level workflows for PDF upload, paper review, summary generation, search, clustering, recommendations, deletion, and PDF report export.

---

## Core Features

* React and Vite frontend architecture
* Tailwind CSS styling with a custom bronze-accent palette
* Modular `components/` and `pages/` structure
* Multi-file PDF upload with drag-and-drop support
* Upload-progress, processing, failure, and completion states
* Completed-upload PDF previews
* Stored-paper browsing and metadata inspection
* Keyword, semantic, and hybrid search modes
* Relevance-score display for ranked search results
* Detailed paper views with abstractive summary generation
* CPU and GPU execution-status notice for summary generation
* Related-paper recommendations
* Topic-cluster exploration with filtering and sorting
* Individual and bulk document deletion
* Configurable PDF report export

---

## Directory Structure

```text
frontend/
├── index.html                 # Vite HTML entry point
├── public/
│   ├── README.md              # Public-asset documentation
│   └── vite.svg               # Placeholder browser favicon
├── src/
│   ├── components/
│   │   ├── README.md          # Reusable-component documentation
│   │   ├── Navbar.jsx         # Global navigation bar
│   │   ├── Dropzone.jsx       # PDF upload and preview component
│   │   ├── Card.jsx           # Reusable content wrapper
│   │   ├── Button.jsx         # Reusable button variants
│   │   ├── Table.jsx          # Generic table utility
│   │   └── Modal.jsx          # Accessible modal utility
│   ├── pages/
│   │   ├── README.md          # Page-level workflow documentation
│   │   ├── UploadPage.jsx     # Upload workflow
│   │   ├── AllPapersPage.jsx  # Paper browsing, search, and deletion
│   │   ├── FullSummary.jsx    # Detailed metadata and summary generation
│   │   ├── ClusterPage.jsx    # Cluster exploration
│   │   └── ExportPage.jsx     # PDF report export
│   ├── api.js                 # Shared Axios API helpers
│   ├── App.jsx                # Root router and shared layout
│   ├── main.jsx               # React entry point and BrowserRouter setup
│   ├── index.css              # Tailwind directives and shared custom styles
│   └── README.md              # Frontend source documentation
├── package.json               # Frontend scripts and dependencies
├── package-lock.json          # Locked npm dependency versions
├── vite.config.js             # Vite configuration
├── tailwind.config.cjs        # Tailwind theme configuration
├── postcss.config.cjs         # PostCSS and Autoprefixer configuration
└── README.md                  # Frontend documentation
```

---

## Technology Stack

| Technology                   | Purpose                                                             |
| ---------------------------- | ------------------------------------------------------------------- |
| **React**                    | Provides the component-based user interface.                        |
| **Vite**                     | Provides the development server and production build pipeline.      |
| **Tailwind CSS**             | Provides utility-first styling and the bronze-accent design system. |
| **React Router DOM**         | Handles client-side navigation between frontend routes.             |
| **Axios**                    | Handles communication with the FastAPI backend.                     |
| **React PDF Viewer**         | Displays uploaded PDFs in the frontend preview workflow.            |
| **PostCSS and Autoprefixer** | Support frontend CSS processing.                                    |

---

## Setup and Run

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the Vite development server:

```bash
npm run dev
```

Open the frontend at:

```text
http://localhost:5173
```

Start the FastAPI backend separately at:

```text
http://127.0.0.1:8000
```

---

## API Configuration

The shared API module in `src/api.js` uses the following environment variable when configured:

```text
VITE_API_URL
```

When the variable is not configured, shared API helpers fall back to:

```text
http://127.0.0.1:8000
```

Example `.env` configuration:

```text
VITE_API_URL=http://127.0.0.1:8000
```

Some page-specific requests currently use direct Axios calls with the local backend URL. Future refactoring should centralise the remaining requests in `src/api.js` so the environment variable applies consistently across the frontend.

---

## Frontend Route Map

| Route         | Component       | Purpose                                                                         |
| ------------- | --------------- | ------------------------------------------------------------------------------- |
| `/`           | Redirect        | Redirects users to `/upload`.                                                   |
| `/upload`     | `UploadPage`    | Uploads, tracks, and previews PDF documents.                                    |
| `/papers`     | `AllPapersPage` | Browses, searches, inspects, and deletes stored papers.                         |
| `/papers/:id` | `FullSummary`   | Displays detailed metadata, generates summaries, and retrieves recommendations. |
| `/cluster`    | `ClusterPage`   | Displays topic clusters and grouped papers.                                     |
| `/export`     | `ExportPage`    | Configures and downloads PDF reports.                                           |

---

## Frontend-to-Backend Map

| Frontend Workflow          | Backend Endpoint               | Purpose                                                  |
| -------------------------- | ------------------------------ | -------------------------------------------------------- |
| Upload PDF                 | `POST /api/upload`             | Uploads and processes a PDF document.                    |
| List stored papers         | `GET /api/docs`                | Retrieves locally stored document records.               |
| Retrieve document metadata | `GET /api/meta/{id}`           | Retrieves stored and enriched metadata.                  |
| Retrieve extracted text    | `GET /api/text/{id}`           | Retrieves extracted document text.                       |
| Delete document            | `DELETE /api/docs/{id}`        | Deletes a stored paper and related local data.           |
| Keyword search             | `POST /api/search`             | Performs TF-IDF keyword search.                          |
| Semantic search            | `POST /api/semantic_search`    | Performs transformer-based semantic search.              |
| Hybrid search              | `POST /api/hybrid_search`      | Combines keyword and semantic-search scores.             |
| Retrieve clusters          | `GET /api/clustered`           | Retrieves clustered paper groups and keywords.           |
| Generate summary           | `POST /api/summarize/{id}`     | Generates a short, medium, or long abstractive summary.  |
| Save generated summary     | `PATCH /api/meta/{id}/summary` | Replaces the stored summary.                             |
| Retrieve recommendations   | `GET /api/external_recs/{id}`  | Retrieves related-paper recommendations where available. |
| Check GPU availability     | `GET /api/system/gpu`          | Reports whether CUDA acceleration is available.          |
| Export report              | `POST /api/export`             | Generates and returns a configurable PDF report.         |

---

## Workflow Summary

### Upload

Users can select or drag multiple PDF files into the upload area. The interface tracks upload progress and backend-processing state, reports failures, and allows completed files to be previewed locally.

### Browse and Search

The All Papers page retrieves stored documents and metadata, then supports keyword, semantic, and hybrid search. Ranked results display relevance scores alongside titles, filenames, summaries, authors, and publication years.

### Generate Summaries

The Full Summary page displays detailed metadata and supports short, medium, or long abstractive-summary generation. Generated summaries can replace the stored summary. The page also reports when GPU acceleration is unavailable and CPU execution may take longer.

### Explore Clusters

The Cluster page retrieves generated topic clusters and maps document IDs to stored paper records. Users can filter, sort, and inspect grouped papers.

### Export Reports

The Export page allows users to configure report sections, including paper lists, cluster overviews, grouped papers, summaries, keywords, charts, and optional recommendations.

PDF is the supported final export format. CSV and JSON options remain visible as disabled future options.

---

## Available Scripts

| Command           | Purpose                                |
| ----------------- | -------------------------------------- |
| `npm run dev`     | Starts the Vite development server.    |
| `npm run build`   | Creates the production frontend build. |
| `npm run lint`    | Runs ESLint checks.                    |
| `npm run preview` | Previews the production build locally. |

---

## Production Build

Create the production build:

```bash
npm run build
```

Preview the generated build locally:

```bash
npm run preview
```

---

## Implementation Notes

* `main.jsx` mounts the application and wraps it in `BrowserRouter`.
* `App.jsx` provides the shared navigation bar and route declarations.
* `src/api.js` contains reusable Axios helpers for common backend requests.
* Some specialised page requests still use direct Axios calls and should be centralised in a future refactor.
* The frontend uses local React state and props rather than a global state-management library.
* The bronze colour palette is configured in `tailwind.config.cjs`.
* The current public favicon remains the default Vite logo and can be replaced with a SmartResearch-specific asset in a future interface update.
