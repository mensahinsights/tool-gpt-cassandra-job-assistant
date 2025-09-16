#!/usr/bin/env python3
import argparse, pathlib, re, json, sys

OVERLAYS = {
    "cpg": "includes/overlays/cpg.md",
    "retail": "includes/overlays/retail.md",
    "healthcare": "includes/overlays/healthcare.md",
    "logistics": "includes/overlays/logistics.md",
    "fintech": "includes/overlays/fintech.md",
    "saas": "includes/overlays/saas.md",
}

def pick_overlay(base: pathlib.Path, domain: str) -> dict:
    p = base / OVERLAYS[domain]
    text = p.read_text(encoding="utf-8")
    # naive parsing
    headline = re.findall(r"## Headline options\n((?:- .+\n)+)", text)[0].strip().splitlines()
    summary = re.findall(r"## Summary starters\n((?:- .+\n)+)", text)[0].strip().splitlines()
    core = re.findall(r"## Core Skills\n(.+)", text)[0].split(",")
    return {
        "headline": [h[2:] for h in headline],
        "summary": [s[2:] for s in summary],
        "core": [c.strip() for c in core]
    }

def main():
    ap = argparse.ArgumentParser(description="Create an MTO pack in a run folder")
    ap.add_argument("run_path", help="Path to runs/YYYY-MM-DD_Company_Role")
    ap.add_argument("--domain", required=True, choices=list(OVERLAYS.keys()), help="Domain overlay to use")
    args = ap.parse_args()

    base = pathlib.Path(__file__).resolve().parents[1]
    run = (base / args.run_path).resolve()
    if not run.exists():
        raise SystemExit(f"Run folder not found, {run}")
    overlay = pick_overlay(base, args.domain)

    out = run / "outputs" / "mto_pack.md"
    content = f"# MTO pack, {args.domain}\n\n"
    content += "## Headline\n" + overlay["headline"][0] + "\n\n"
    content += "## Summary\n- " + "\n- ".join(overlay["summary"]) + "\n\n"
    content += "## Three bullets\n"
    # pick three generic bullets
    content += "- Increased <metric> by <x> using <method>, which improved <KPI>.\n"
    content += "- Reduced <time or cost> by <x> with <tool>, enabling <benefit>.\n"
    content += "- Built <artifact> for <stakeholder> that <action>, resulting in <impact>.\n\n"
    content += "## Core Skills\n" + ", ".join(overlay["core"][:10]) + "\n\n"
    content += "## Next\n- Paste two must have JD terms into the Summary.\n- Swap nouns to match the JD.\n- Export and submit.\n"
    out.write_text(content, encoding="utf-8")
    print(str(out))

if __name__ == "__main__":
    main()
