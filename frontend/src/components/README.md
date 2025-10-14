# SmartResearch — Frontend Components

This directory contains all **reusable UI components** for the SmartResearch web app.  
They follow a consistent design system using **Tailwind CSS**.

---

## Component Overview

| Component | Purpose |
|------------|----------|
| `Navbar.jsx` | Global top navigation bar with page links (Upload, All Papers, Cluster, Export). |
| `Dropzone.jsx` | Handles PDF upload via drag-and-drop or file picker, with progress bars, status tracking, and live previews. |
| `Card.jsx` | Base container for visual grouping — consistent rounded/shadowed UI block. |
| `Button.jsx` | Reusable button component supporting `primary`, `secondary`, and `ghost` variants. |
| `Table.jsx` | Generic, responsive table for displaying datasets (e.g. uploaded papers or search results). |
| `Modal.jsx` | Accessible modal window supporting default and large view modes. |

---

## Design & Conventions

- Built with **React functional components** and **Tailwind utility classes**.  
- Uses bronze-toned accent colours (`bg-bronze-*`) for visual branding consistency.  
- All components are self-contained — no external state management libraries.  

---

## Integration Notes

- All upload actions in `Dropzone.jsx` connect to the backend endpoint  
  `POST http://127.0.0.1:8000/api/upload`.  
- Tables and modals can later fetch data from `/api/search`, `/api/clustered`, or `/api/text/{doc_id}`.  
- `Navbar` routes rely on `react-router-dom` and should align with `App.jsx` routing map.

---

## Example Usage

```jsx
import Dropzone from "../components/Dropzone";
import Table from "../components/Table";
import Modal from "../components/Modal";

export default function UploadPage() {
  return (
    <div className="p-6 space-y-6">
      <Dropzone />
      <Table columns={[{ header: "Title", accessor: "title" }]} data={[]} />
      <Modal open={false} title="Details"></Modal>
    </div>
  );
}
