# SmartResearch — Public Assets

The `public/` directory contains static assets served directly by the Vite frontend.

Files stored in this directory are copied into the final build output without being processed by the React bundling pipeline. They can be referenced using root-relative paths.

---

## Contents

| File       | Purpose                                                              |
| ---------- | -------------------------------------------------------------------- |
| `vite.svg` | Default Vite logo currently used as the placeholder browser favicon. |

---

## Usage Notes

* Files in `public/` are accessible through root-relative paths, such as `/vite.svg`.
* Static assets such as favicons, logos, manifest files, and other files that do not require bundling may be stored here.
* Assets from this directory should be referenced by their public URL rather than imported into React components.
* The placeholder Vite favicon can be replaced with a SmartResearch-specific asset in a future interface update.

---

## Structure

```text
public/
├── vite.svg
└── README.md
```
