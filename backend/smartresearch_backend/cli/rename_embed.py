import argparse, os
from smartresearch_backend.libs.pdf_rename_embed import rename_folder

def main():
    ap = argparse.ArgumentParser(description="Rename PDFs and embed Title/Author (+year dates).")
    ap.add_argument("folder", help="Folder containing .pdf files")
    ap.add_argument("--apply", action="store_true", help="Actually rename files (default: dry-run)")
    ap.add_argument("--pages", type=int, default=1, help="Read first N pages (1–2 recommended)")
    ap.add_argument("--mode", choices=["auto","structured","heuristic"], default="auto", help="Extraction strategy")
    args = ap.parse_args()

    assert os.path.isdir(args.folder), f"Not a directory: {args.folder}"

    for status, old, new, title, authors, year in rename_folder(
        args.folder, apply=args.apply, pages=args.pages, mode=args.mode
    ):
        if status == "dry":
            print(f"[DRY] {old} → {new}")
            print(f"      title={title or old} | author={authors or 'Unknown'} | year={year or 'n/a'}")
        else:
            print(f"[✔] {old} → {new} (metadata embedded)")

if __name__ == "__main__":
    main()
