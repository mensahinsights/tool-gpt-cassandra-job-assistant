import os
import sys
import json
import datetime
import re
from pathlib import Path
from openai import OpenAI

BASELINES_PATH = "baselines.json"

def load_baselines():
    with open(BASELINES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def sanitize_text(text: str) -> str:
    """Replace forbidden characters and normalize whitespace with ASCII-safe approach."""
    # Character code mappings for better GitHub Actions compatibility
    char_map = {
        8212: "-",    # em dash
        8211: "-",    # en dash
        8220: '"',    # left double quotation mark
        8221: '"',    # right double quotation mark
        8217: "'",    # right single quotation mark
        8216: "'",    # left single quotation mark
        8226: "*",    # bullet point
    }
    
    # Replace by character codes first
    for code, replacement in char_map.items():
        text = text.replace(chr(code), replacement)
    
    # Fallback regex for any remaining problematic unicode
    text = re.sub(r'[^\x00-\x7F]+', '-', text)
    
    # Normalize whitespace
    return " ".join(text.split())

def generate_tailored_bullets(role: str, job_title: str, company: str, api_key: str):
    """Generate tailored bullets with OpenAI, fallback to baseline if needed."""
    try:
        client = OpenAI(api_key=api_key)
        prompt = (
            f"Generate 4-6 strong resume bullet points for the role '{role}' "
            f"that align with the job title '{job_title}' at {company}. "
            "Each bullet must begin with a strong action verb, be specific, "
            "and highlight measurable impact where possible. Return only the bullets."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        bullets = [
            sanitize_text(line.strip("*- ").strip())  # ASCII-safe stripping
            for line in resp.choices[0].message.content.splitlines()
            if line.strip()
        ]
        return bullets[:6] if bullets else None
    except Exception as e:
        print(f"[WARN] OpenAI bullet gen failed for {role}: {e}")
        return None

def build_resume(jd_path: Path, baselines: dict):
    """Generate resume markdown and result.json metadata."""
    folder_name = jd_path.parent.parent.name
    parts = folder_name.split("_", 1)
    company = parts[-1] if len(parts) > 1 else folder_name
    job_title = company.replace("_", " ")

    api_key = os.environ.get("OPENAI_API_KEY")
    roles_data = {}
    resume_md = []

    # Contact block
    contact = baselines.get("contact", {})
    resume_md.append(f"# {contact.get('name', 'Gamal Mensah')}")
    resume_md.append(f"{contact.get('location', 'Toronto, ON')} | {contact.get('email', '')} | {contact.get('phone', 'Phone on request')}")
    if contact.get("linkedin"):
        resume_md.append(f"[LinkedIn]({contact['linkedin']}) | [Portfolio]({contact.get('portfolio', '')})")
    resume_md.append("")

    # Summary
    summary = baselines.get("summary", [])
    if summary:
        resume_md.append("## Summary")
        for line in summary:
            resume_md.append(f"- {sanitize_text(line)}")
        resume_md.append("")

    # Experience
    resume_md.append("## Professional Experience")
    for role, details in baselines.get("experience", {}).items():
        title = details.get("title", role)
        employer = details.get("employer", "")
        dates = details.get("dates", "")
        location = details.get("location", "")
        resume_md.append(f"### {title} | {employer}")
        resume_md.append(f"{dates} | {location}")

        bullets = []
        if api_key:
            bullets = generate_tailored_bullets(role, job_title, company, api_key)
        if not bullets:
            bullets = details.get("bullets", [])
        bullets = [sanitize_text(b) for b in bullets]
        if len(bullets) < 4:
            bullets += details.get("bullets", [])
        bullets = bullets[:6]

        for b in bullets:
            resume_md.append(f"- {b}")
        resume_md.append("")

        roles_data[role] = bullets

    # Education
    resume_md.append("## Education")
    for edu in baselines.get("education", []):
        resume_md.append(f"- {sanitize_text(edu)}")
    resume_md.append("")

    # Skills
    resume_md.append("## Skills")
    for skill in baselines.get("skills", []):
        resume_md.append(f"- {sanitize_text(skill)}")
    resume_md.append("")

    # Write outputs with explicit encoding
    out_dir = jd_path.parent.parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_file = out_dir / f"Gamal_Mensah_Resume_{company}.md"
    
    # Ensure ASCII-safe output for GitHub Actions
    resume_content = "\n".join(resume_md)
    with open(md_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(resume_content)
    print(f"[DEBUG] Wrote resume: {md_file}")

    # Metadata for Sheets (EXACT 7 fields, nothing else)
    result = {
        "date": datetime.date.today().isoformat(),
        "company": company,
        "job_title": job_title,
        "jd_path": str(jd_path),
        "closing_date": "TBD Closing Date",
        "jd_url": "",
        "ats_score": "fallback"
    }
    result_path = out_dir / "result.json"
    with open(result_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, ensure_ascii=True)  # Force ASCII output
    print(f"[DEBUG] Wrote metadata: {result_path}")

    # Marker for workflow
    marker_path = Path(".last_result")
    with open(marker_path, "w", encoding="utf-8", newline="\n") as marker:
        marker.write(str(result_path))
    print(f"[DEBUG] Wrote marker file: {marker_path} -> {result_path}")

def main(jd_path: str):
    baselines = load_baselines()
    build_resume(Path(jd_path), baselines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_resume_from_jd.py <jd.md>")
        sys.exit(1)
    main(sys.argv[1])