# SmartResearch — Frontend Source

The `src/` directory contains all **core source files** for the SmartResearch frontend.  
Built with **React (Vite)** and styled using **Tailwind CSS**, it provides the user interface for document upload, search, clustering, and export — integrating seamlessly with the FastAPI backend.

---

## Directory Structure
```markdown
src/
├── components/ # Reusable UI elements (buttons, modals, tables, cards, dropzones)
├── pages/ # Top-level page views (Upload, All Papers, Cluster, Export)
├── App.jsx # Root router and layout composition
├── main.jsx # React entrypoint (creates root and mounts <App />)
├── index.css # Global Tailwind and custom style definitions
└── assets/ (optional) # Static images, icons, or local assets
```
---

## Tech Stack

| Layer | Description |
|-------|--------------|
| **React + Vite** | Lightweight development environment for fast iteration. |
| **Tailwind CSS** | Utility-first styling system for responsive design. |
| **React Router DOM** | Handles client-side navigation between pages. |
| **Axios / Fetch API** | Manages communication with FastAPI backend endpoints. |
| **shadcn/ui (optional)** | Future-ready UI components for enhanced polish. |

---

## Architecture

| Layer | Purpose |
|-------|----------|
| **Components** | Encapsulated, reusable UI units for consistency and scalability. |
| **Pages** | Route-level screens that combine components into workflows. |
| **App.jsx** | Declares route structure and global layout. |
| **Backend Integration** | Uses REST API calls to `/api/upload`, `/api/search`, `/api/clustered`, etc. |
| **Styling Layer** | Controlled via Tailwind, following the same bronze-accent palette as backend branding. |

---

## Development Workflow

Run the frontend in dev mode (after installing dependencies):

```bash
cd frontend
npm install
npm run dev
```
This starts the Vite server on http://localhost:5173 

The React app communicates with the backend API at http://127.0.0.1:8000.

--- 

Interaction Flow

Upload Page → sends PDF to /api/upload.

All Papers Page → fetches /api/docs, /api/search, or /api/text/{id}.

Cluster Page → retrieves /api/clustered or /api/semantic_search.

Export Page → prepares user-selected clusters for report generation.

---

Example Route Map
```markdown 
Route	Component	Purpose
/upload	UploadPage	Upload and preview new documents.
/all	AllPapersPage	View, search, and inspect all stored papers.
/cluster	ClusterPage	Display clustered research themes and summaries.
/export	ExportPage	Compile and export cluster-based reports.
```
