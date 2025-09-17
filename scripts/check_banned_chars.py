import sys
import pathlib

if len(sys.argv) < 2:
    print("Usage: python check_banned_chars.py <path>")
    sys.exit(1)

base_path = pathlib.Path(sys.argv[1])

for file in base_path.rglob("*"):
    if file.is_file():
        text = file.read_text(encoding="utf-8", errors="ignore")
        if "—" in text:  # em dash
            raise ValueError(f"[ban] {file} contains forbidden character '—\u2014'")
