# SmartResearch — Frontend

The **SmartResearch Frontend** provides the user interface for interacting with the FastAPI backend.  
It’s built with **React (Vite)** and styled with **Tailwind CSS**, designed for fast iteration, responsive layouts, and seamless backend integration.

---

## Core Features

- Modern React architecture (Vite + JSX)
- Modular component structure (`components/` + `pages/`)
- RESTful backend communication via Fetch or Axios
- Dynamic PDF upload, clustering, and summarization workflows
- Responsive, clean UI with bronze-accent theme consistency

---

## Directory Structure
```markdown
frontend/
├── src/
│ ├── components/ # Reusable UI components
│ ├── pages/ # Route-level views (Upload, All Papers, Cluster, Export)
│ ├── App.jsx # Root app router and layout
│ ├── main.jsx # React entrypoint (creates root and mounts <App />)
│ ├── index.css # Global Tailwind and style definitions
│ └── assets/ (optional) # Local icons or images
├── public/ # Static assets (vite.svg, favicon, etc.)
├── package.json # Dependencies
├── vite.config.js # Vite build configuration
├── tailwind.config.cjs # Tailwind theme setup
├── postcss.config.cjs # PostCSS configuration
└── README.md # Frontend documentation
```

---

## Setup & Run

Install dependencies and start the dev server:

```bash
cd frontend
npm install
npm run dev
```

Access the app locally at:  
**http://localhost:5173**

Ensure your backend is running at:  
**http://127.0.0.1:8000**

---

## Frontend ↔ Backend Map

| Frontend Route | Backend Endpoint | Function |
|----------------|------------------|-----------|
| `/upload` | `/api/upload` | Upload and parse PDF |
| `/all` | `/api/docs`, `/api/search` | View and search stored papers |
| `/cluster` | `/api/clustered` | Retrieve clustered topics |
| `/export` | `/api/export` *(future)* | Generate cluster reports |

