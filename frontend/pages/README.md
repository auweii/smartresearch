# SmartResearch — Page Views

This directory contains all **top-level pages** for the SmartResearch frontend.  
Each page represents a full route in the app and orchestrates the flow between backend endpoints and UI components.  
Together, they form the user-facing workflows for uploading, viewing, clustering, and exporting research papers.

---

## Directory Overview
```markdown
src/pages/
├── UploadPage.jsx # Handles PDF upload, preview, and backend integration
├── AllPapersPage.jsx # Displays searchable table of all uploaded documents
├── ClusterPage.jsx # Groups documents by topic; visualises clusters
└── ExportPage.jsx # Generates exportable summaries or reports
```

---

## Page Responsibilities

| Page | Description |
|------|--------------|
| **UploadPage** | Entry point for uploading PDFs. Connects to `/api/upload` and displays extracted metadata + preview text using `Dropzone` and `Card` components. |
| **AllPapersPage** | Lists all stored documents using `Table`. Supports keyword search and score-based ranking via `/api/search` or `/api/semantic_search`. |
| **ClusterPage** | Fetches clustered document data from `/api/clustered`. Displays summaries and topic groups using modular cards. |
| **ExportPage** | Allows users to export selected clusters or summaries (future integration with `/api/move_to_storage` or report generator). |

---

## Architecture Notes

- Each page is a **React functional component**.  
- Layout follows the same design rhythm — padding, spacing, bronze-accent UI from `components/`.  
- Routes are defined in `App.jsx` via `react-router-dom`.  
- Pages import only the necessary UI components; no global state is used.  
- Communication with the backend happens through **fetch** or **axios** calls using local endpoint URLs (e.g. `http://127.0.0.1:8000/api/...`).  

---

## Example Route Integration

```jsx
import { Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import AllPapersPage from "./pages/AllPapersPage";
import ClusterPage from "./pages/ClusterPage";
import ExportPage from "./pages/ExportPage";

export default function App() {
  return (
    <Routes>
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/all" element={<AllPapersPage />} />
      <Route path="/cluster" element={<ClusterPage />} />
      <Route path="/export" element={<ExportPage />} />
    </Routes>
  );
}
```

