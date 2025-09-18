#!/usr/bin/env python3
import os
import sys
import json
import datetime
import re
from pathlib import Path
import openai  # use the modern SDK

BASELINES_PATH = "baselines.json"

def load_baselines():
    with open(BASELINES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def sanitize_text(text: str) -> str:
    """Replace forbidden characters in plain text while preserving Markdown syntax."""
    char_map = {
        8212: "-",    # em dash → hyphen
        8211: "-",    # en dash → hyphen
        8220: '"',    # left double quote
        8221: '"',    # right double quote
        8217: "'",    # right single quote
        8216: "'",    # left single quote
        8226: "*",    # bullet point
    }
    for code, replacement in char_map.items():
        text = text.replace(chr(code), replacement)
    text = re.sub(r'[^\x00-\x7F]', '', text)   # strip non-ASCII
    text = re.sub(r'[ \t]+', ' ', text).strip()
    return text

def parse_jd_header(jd_path: Path):
    """Parse structured header from jd.md file."""
    try:
        with open(jd_path, "r", encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---"):
            parts = content.split("---")
            header_section = parts[1].strip() if len(parts) > 2 else parts[0].strip()
        else:
            header_section = content.split("---")[0].strip()
        data = {}
        for line in header_section.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                if value:
                    data[key] = sanitize_text(value)
        print(f"[DEBUG] Parsed JD header: {data}")
        return data
    except Exception as e:
        print(f"[WARN] Failed to parse JD header: {e}")
        return {}

def generate_tailored_bullets(role: str, job_title: str, company: str):
    """Generate tailored bullets with OpenAI, fallback to baseline if needed."""
    try:
        prompt = (
            f"Generate 4-6 strong resume bullet points for the role '{role}' "
            f"that align with the job title '{job_title}' at {company}. "
            "Each bullet must begin with a strong action verb, be specific, "
            "and highlight measurable impact where possible. Return only the bullets."
        )
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        bullets = [
            sanitize_text(line.strip("*- ").strip())
            for line in resp.choices[0].message.content.splitlines()
            if line.strip()
        ]
        return bullets[:6] if bullets else None
    except Exception as e:
        print(f"[WARN] OpenAI bullet gen failed for {role}: {e}")
        return None

def build_resume(jd_path: Path, baselines: dict):
    jd_data = parse_jd_header(jd_path)
    folder_name = jd_path.parent.parent.name
    folder_parts = folder_name.split("_", 1)
    fallback_company = folder_parts[-1] if len(folder_parts) > 1 else folder_name
    company = jd_data.get("company", fallback_company)
    job_title = jd_data.get("job_title", company.replace("_", " "))
    jd_url = jd_data.get("url", "")
    closing_date = jd_data.get("closing_date", "")

    print(f"[DEBUG] Using: Company='{company}', Job Title='{job_title}', URL='{jd_url}'")
    api_key_present = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    print(f"[DEBUG] OpenAI API key present: {api_key_present}")
    if api_key_present:
        print(f"[DEBUG] OpenAI API key length: {len(os.environ.get('OPENAI_API_KEY'))}")

    roles_data = {}
    resume_md = []

    # Contact block
    contact = baselines.get("contact", {})
    name = contact.get("name", "Gamal Mensah")
    location = contact.get("location", "Toronto, ON")
    email = contact.get("email", "gmensah.analytics@gmail.com")
    phone = contact.get("phone", "Phone: Provided on request")
    linkedin = contact.get("linkedin", "")
    portfolio = contact.get("portfolio", "")
    resume_md.append(f"# {name}")
    resume_md.append(f"{location} | {email} | {phone}")
    if linkedin and portfolio:
        resume_md.append(f"[LinkedIn]({linkedin}) · [Portfolio]({portfolio})")
    elif linkedin:
        resume_md.append(f"[LinkedIn]({linkedin})")
    elif portfolio:
        resume_md.append(f"[Portfolio]({portfolio})")
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
    experience_data = baselines.get("experience", {})
    print(f"[DEBUG] Found {len(experience_data)} experience roles: {list(experience_data.keys())}")
    for role, details in experience_data.items():
        print(f"[DEBUG] Processing role: {role}")
        title = details.get("title", role)
        employer = details.get("employer", "")
        dates = details.get("dates", "")
        location = details.get("location", "")
        resume_md.append(f"### {title} | {employer}")
        resume_md.append(f"{dates} | {location}")

        bullets = []
        if api_key_present:
            print(f"[DEBUG] Attempting OpenAI bullet generation for {role}")
            bullets = generate_tailored_bullets(role, job_title, company)
            if bullets:
                print(f"[DEBUG] Generated {len(bullets)} OpenAI bullets for {role}")
            else:
                print(f"[WARN] OpenAI bullet generation failed for {role}, using fallback")
        else:
            print(f"[DEBUG] No OpenAI API key found, using baseline bullets for {role}")

        if not bullets:
            bullets = details.get("bullets", [])
            print(f"[DEBUG] Using {len(bullets)} baseline bullets for {role}")

        bullets = [sanitize_text(b) for b in bullets]
        if len(bullets) < 4:
            baseline_bullets = details.get("bullets", [])
            bullets.extend(baseline_bullets)
            print(f"[DEBUG] Extended to {len(bullets)} total bullets for {role}")
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

    # Write outputs
    out_dir = jd_path.parent.parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_file = out_dir / f"Gamal_Mensah_Resume_{company.replace(' ', '_')}.md"
    resume_content = "\n".join(resume_md)
    with open(md_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(resume_content)
    print(f"[DEBUG] Wrote resume: {md_file}")

    result = {
        "date": datetime.date.today().isoformat(),
        "company": sanitize_text(company),
        "job_title": sanitize_text(job_title),
        "jd_path": str(jd_path),
        "closing_date": sanitize_text(closing_date) if closing_date else "TBD Closing Date",
        "jd_url": sanitize_text(jd_url),
        "ats_score": "fallback"
    }
    result = {k: sanitize_text(str(v)) if isinstance(v, str) else v for k, v in result.items()}

    result_path = out_dir / "result.json"
    with open(result_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, ensure_ascii=True)
    print(f"[DEBUG] Wrote metadata: {result_path}")
    print(f"[DEBUG] Result JSON content: {result}")

    marker_path = Path(".last_result")
    abs_result_path = result_path.absolute()
    timestamp = datetime.datetime.now().isoformat()
    with open(marker_path, "w", encoding="utf-8", newline="\n") as marker:
        marker.write(f"{abs_result_path}|{timestamp}")
    print(f"[DEBUG] Wrote marker file: {marker_path} -> {abs_result_path} at {timestamp}")

def main(jd_path: str):
    baselines = load_baselines()
    build_resume(Path(jd_path), baselines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_resume_from_jd.py <jd.md>")
        sys.exit(1)
    main(sys.argv[1])
