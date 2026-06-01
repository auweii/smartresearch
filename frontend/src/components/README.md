# SmartResearch — Frontend Components

This directory contains reusable React UI components used across the SmartResearch frontend.

The components follow the shared Tailwind CSS design system and bronze-toned visual palette defined for the application.

---

## Component Overview

| Component      | Purpose                                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Navbar.jsx`   | Global top navigation bar with links to Upload, All Papers, Cluster, and Export.                                                                              |
| `Dropzone.jsx` | Handles multi-file PDF selection and drag-and-drop upload, progress tracking, processing states, failure states, file removal, and completed-upload previews. |
| `Card.jsx`     | Lightweight wrapper used to group interface content while allowing page-specific styling through `className`.                                                 |
| `Button.jsx`   | Reusable button wrapper supporting `primary`, `secondary`, and `ghost` variants.                                                                              |
| `Table.jsx`    | Generic responsive table component accepting column definitions, data rows, and an optional row-click handler.                                                |
| `Modal.jsx`    | Reusable modal component with accessible dialog attributes and support for default and large display modes.                                                   |

---

## Component Details

### `Navbar.jsx`

Provides the persistent application navigation bar.

The component uses `NavLink` from `react-router-dom` and links to:

```text id="kyv3ht"
/upload
/papers
/cluster
/export
```

The active route is visually highlighted.

---

### `Dropzone.jsx`

Provides the upload interface used by the Upload page.

The component supports:

* Selecting one or more PDF files through the file picker
* Dragging and dropping multiple PDF files
* Upload-progress tracking
* Uploading, processing, completed, and failed states
* Removing files from the local upload list
* Previewing completed uploads in an embedded PDF viewer
* Reporting selected files to the parent page through the `onFiles` callback

Uploads are delegated to `uploadPaper()` from `../api.js`.

---

### `Card.jsx`

Provides a lightweight content wrapper:

```jsx id="8i6s2l"
<Card className="p-6 rounded-3xl shadow-sm">
  <p>Content</p>
</Card>
```

The component applies the shared `card` class and accepts additional page-specific Tailwind classes through `className`.

---

### `Button.jsx`

Provides a reusable button wrapper with the following variants:

| Variant     | CSS Class       |
| ----------- | --------------- |
| `primary`   | `btn-primary`   |
| `secondary` | `btn-secondary` |
| `ghost`     | `btn-ghost`     |

Example:

```jsx id="dpdv7q"
<Button variant="primary" onClick={handleSubmit}>
  Submit
</Button>
```

---

### `Table.jsx`

Provides a generic table for reusable dataset display.

The component accepts:

| Prop         | Purpose                                                    |
| ------------ | ---------------------------------------------------------- |
| `columns`    | Array of column definitions using `header` and `accessor`. |
| `data`       | Array of row objects.                                      |
| `onRowClick` | Optional callback invoked when a row is selected.          |

The component displays an empty-state message when no rows are available.

---

### `Modal.jsx`

Provides a reusable modal window with:

* `role="dialog"`
* `aria-modal="true"`
* A labelled modal title
* Backdrop-click closing
* Default and large display modes
* Optional header rendering for the default mode

Example:

```jsx id="7mcgqq"
<Modal
  open={isOpen}
  title="Paper Details"
  onClose={() => setIsOpen(false)}
  size="default"
>
  <p>Paper information</p>
</Modal>
```

---

## Design System

* Components are built with React functional components.
* Styling uses Tailwind CSS utility classes.
* The frontend uses a custom bronze colour palette configured in `tailwind.config.cjs`.
* Shared button styles are defined in `src/index.css`.
* Components use local React state and props rather than an external state-management library.

---

## API Integration

The upload component imports `uploadPaper()` from `../api.js`.

The shared API module:

* Uses `VITE_API_URL` when configured
* Falls back to `http://127.0.0.1:8000`
* Creates a reusable Axios instance with the `/api` prefix
* Exposes helpers for upload, document retrieval, deletion, metadata, text retrieval, clustering, keyword search, semantic search, hybrid search, and PDF export

The resulting upload request is sent to:

```text id="4ya5gi"
POST /api/upload
```

---

## Routing Integration

`Navbar.jsx` aligns with the primary routes declared in `App.jsx`:

| Route         | Page              |
| ------------- | ----------------- |
| `/upload`     | Upload page       |
| `/papers`     | All Papers page   |
| `/papers/:id` | Full Summary page |
| `/cluster`    | Cluster page      |
| `/export`     | Export page       |

---

## Example Usage

```jsx id="72lx44"
import { useState } from "react";
import Card from "../components/Card";
import Dropzone from "../components/Dropzone";
import Modal from "../components/Modal";

export default function ExamplePage() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card className="p-6 space-y-4">
      <Dropzone />

      <button
        className="btn-primary"
        onClick={() => setIsOpen(true)}
      >
        Open Details
      </button>

      <Modal
        open={isOpen}
        title="Paper Details"
        onClose={() => setIsOpen(false)}
      >
        <div className="p-4">
          Example modal content.
        </div>
      </Modal>
    </Card>
  );
}
```

---

## Current Usage Note

`Navbar.jsx`, `Dropzone.jsx`, `Card.jsx`, and `Modal.jsx` are integrated into the current frontend workflow.

`Button.jsx` and `Table.jsx` remain available as reusable UI utilities. Some current pages render specialised buttons and tables directly where page-specific behaviour is required.
