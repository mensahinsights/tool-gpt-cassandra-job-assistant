#!/usr/bin/env python3
import argparse, pathlib, datetime, re, shutil

def slug(s):
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s[:80]

def main():
    ap = argparse.ArgumentParser(description="Create a new Cassandra run folder")
    ap.add_argument("--company", required=True, help="Company name")
    ap.add_argument("--role", required=True, help="Role title")
    ap.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    args = ap.parse_args()

    date = args.date or datetime.date.today().isoformat()
    base = pathlib.Path(__file__).resolve().parents[1]
    src = base / "runs" / "_run_template"
    if not src.exists():
        raise SystemExit("Template folder runs/_run_template missing")
    folder = f"{date}_{slug(args.company)}_{slug(args.role)}"
    dst = base / "runs" / folder
    if dst.exists():
        raise SystemExit(f"Destination already exists, {dst}")
    shutil.copytree(src, dst)
    # write notes
    notes = (dst / "inputs" / "notes.md")
    text = notes.read_text(encoding="utf-8")
    text = text.replace("Company, ", f"Company, {args.company}")
    text = text.replace("Role, ", f"Role, {args.role}")
    notes.write_text(text, encoding="utf-8")
    print(str(dst))

if __name__ == "__main__":
    main()
