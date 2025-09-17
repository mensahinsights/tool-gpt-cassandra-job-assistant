#!/usr/bin/env python3
import sys, pathlib

BAN = ["\u2014"]  # em dash

def scan(path: pathlib.Path) -> int:
    bad = 0
    for p in path.rglob("*"):
        if p.is_dir():
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".docx"}:
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for ch in BAN:
            if ch in s:
                print(f"[ban] {p}: contains forbidden character {repr(ch)}")
                bad += 1
    return bad

if __name__ == "__main__":
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    code = 1 if scan(root) else 0
    if code == 0:
        print("No banned characters found.")
    sys.exit(code)
