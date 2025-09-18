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

def parse_jd_header(jd_path: Path):
    """Parse structured header from jd.md file."""
    try:
        with open(jd_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract header section (before the --- delimiter)
        header_section = content.split("---")[0].strip()
        
        # Parse key-value pairs
        data = {}
        for line in header_section.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                if value:  # Only add non-empty values
                    data[key] = sanitize_text(value)
        
        print(f"[DEBUG] Parsed JD header: {data}")
        return data
    except Exception as e:
        print(f"[WARN] Failed to parse JD header: {e}")
        return {}

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
    # Parse header data first
    jd_data = parse_jd_header(jd_path)
    
    # Use parsed data, fallback to folder name if needed
    folder_name = jd_path.parent.parent.name
    folder_parts = folder_name.split("_", 1)
    fallback_company = folder_parts[-1] if len(folder_parts) > 1 else folder_name
    
    company = jd_data.get("company", fallback_company)
    job_title = jd_data.get("job_title", company.replace("_", " "))
    jd_url = jd_data.get("url", "")
    closing_date = jd_data.get("closing_date", "")
    
    print(f"[DEBUG] Using: Company='{company}', Job Title='{job_title}', URL='{jd_url}'")

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

        # Generate bullets with better error handling
        bullets = []
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        
        if api_key:
            print(f"[DEBUG] Attempting OpenAI bullet generation for {role}")
            bullets = generate_tailored_bullets(role, job_title, company, api_key)
            if bullets:
                print(f"[DEBUG] Generated {len(bullets)} OpenAI bullets for {role}")
            else:
                print(f"[WARN] OpenAI bullet generation failed for {role}, using fallback")
        else:
            print(f"[DEBUG] No OpenAI API key found, using baseline bullets for {role}")
        
        # Fallback to baseline if OpenAI failed or no API key
        if not bullets:
            bullets = details.get("bullets", [])
            print(f"[DEBUG] Using {len(bullets)} baseline bullets for {role}")
        
        # Ensure we have at least 4 bullets
        bullets = [sanitize_text(b) for b in bullets]
        if len(bullets) < 4:
            baseline_bullets = details.get("bullets", [])
            bullets.extend(baseline_bullets)
            print(f"[DEBUG] Extended to {len(bullets)} total bullets for {role}")
        
        bullets = bullets[:6]  # Cap at 6

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
    md_file = out_dir / f"Gamal_Mensah_Resume_{company.replace(' ', '_')}.md"
    
    # Ensure ASCII-safe output for GitHub Actions
    resume_content = "\n".join(resume_md)
    resume_content = sanitize_text(resume_content)  # Global sanitization pass
    with open(md_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(resume_content)
    print(f"[DEBUG] Wrote resume: {md_file}")

    # Metadata for Sheets (EXACT 7 fields with parsed data)
    result = {
        "date": datetime.date.today().isoformat(),
        "company": sanitize_text(company),
        "job_title": sanitize_text(job_title),
        "jd_path": str(jd_path),
        "closing_date": sanitize_text(closing_date) if closing_date else "TBD Closing Date",
        "jd_url": sanitize_text(jd_url),
        "ats_score": "fallback"
    }
    
    # Sanitize all JSON values
    result = {k: sanitize_text(str(v)) if isinstance(v, str) else v for k, v in result.items()}
    
    result_path = out_dir / "result.json"
    with open(result_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, ensure_ascii=True)  # Force ASCII output
    print(f"[DEBUG] Wrote metadata: {result_path}")
    print(f"[DEBUG] Result JSON content: {result}")

    # Marker for workflow - always use absolute path and timestamp
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