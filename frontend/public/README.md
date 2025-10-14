# SmartResearch — Public Assets

The **public/** directory contains all static files served directly by the Vite development server.  
These files are not processed by the React build pipeline — they are copied as-is to the final build output.

---

## Contents

| File | Purpose |
|------|----------|
| `vite.svg` | Default Vite logo used as the current placeholder favicon or splash asset. |

---

## Usage Notes

- All files in `public/` are accessible via root-relative paths (e.g., `/vite.svg`).  
- Static assets such as logos, manifest files, and favicons should live here.  
- React should not `import` from this directory directly — use the public URL instead.

---

## Structure
```markdown
public/
├── vite.svg
└── README.md
```
