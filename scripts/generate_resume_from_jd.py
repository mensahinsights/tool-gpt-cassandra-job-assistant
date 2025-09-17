import os
import sys
import json
import re
from pathlib import Path
from openai import OpenAI

# Paths
BASELINES_PATH = Path("scripts/baselines.json")

# Roles expected in resume
ROLE_HEADINGS = [
    "Independent Data Analyst | BI & Automation Consultant",
    "Senior Transformation Analyst | PepsiCo",
    "IT Analyst - R&D and Product Development | MPAC"
]

MIN_BULLETS = 4
MAX_BULLETS = 6

def normalize_text(text: str) -> str:
    """Replace em/en dashes with hyphen and collapse whitespace."""
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()

def normalize_role_name(name: str) -> str:
    return normalize_text(name).lower()

def load_baselines():
    if not BASELINES_PATH.exists():
        raise FileNotFoundError(f"Baseline file not found at {BASELINES_PATH}")
    with open(BASELINES_PATH, "r", encoding="utf-8") as f:
        baselines = json.load(f)
    return {normalize_role_name(k): v for k, v in baselines.items()}

def parse_jd(jd_path):
    company, job_title, closing_date, jd_url = None, None, "TBD Closing Date", ""
    with open(jd_path, "r", encoding="utf-8") as f:
        for line in f:
            low = line.lower()
            if low.startswith("company:"):
                company = normalize_text(line.split(":", 1)[1].strip())
            elif low.startswith("job title:"):
                job_title = normalize_text(line.split(":", 1)[1].strip())
            elif low.startswith("closing date:"):
                val = line.split(":", 1)[1].strip()
                if val:
                    closing_date = normalize_text(val)
            elif low.startswith("url:"):
                jd_url = line.split(":", 1)[1].strip()
    return company, job_title, closing_date, jd_url

def safe_openai_request(role_title, job_title, company_name):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert resume writer."},
                {"role": "user", "content": (
                    f"Given the past role '{role_title}' and the target role '{job_title}' at {company_name}, "
                    "generate 4–6 resume bullet points showing alignment. "
                    "If no JD-relevance exists, return highlights from the role without inventing new responsibilities. "
                    "Return only bullet points."
                )}
            ],
            timeout=30
        )
        content = resp.choices[0].message.content
        bullets = [normalize_text(b.strip("-• ")) for b in content.split("\n") if b.strip()]
        return bullets
    except Exception as e:
        print(f"[WARN] OpenAI error for {role_title}: {e}")
        return []

def normalize_bullets(openai_bullets, baseline_bullets):
    if openai_bullets and MIN_BULLETS <= len(openai_bullets) <= MAX_BULLETS:
        return openai_bullets, "openai"
    elif baseline_bullets:
        bullets = baseline_bullets[:MAX_BULLETS]
        if len(bullets) < MIN_BULLETS:
            bullets = (bullets * ((MIN_BULLETS // len(bullets)) + 1))[:MIN_BULLETS]
        return bullets, "baseline"
    else:
        return ["(No baseline bullets available)"], "none"

def build_resume(company_name, job_title, closing_date, jd_url, baselines):
    lines = []
    lines.append(f"# Gamal Mensah\n")
    lines.append("**Data Analyst | Strategic Insight & Automation | SQL • Python • Power BI**  ")
    lines.append("Toronto, ON | gmensah.analytics@gmail.com | Phone: Provided on request | LinkedIn | Portfolio\n")
    lines.append("---\n")

    lines.append("## Professional Summary\n")
    lines.append("I turn operational data into insights that drive action, not just observation. "
                 "With over 10 years of experience in data analysis, I specialize in uncovering trends, "
                 "improving processes, and enabling strategy through automation and clear storytelling.\n")
    lines.append("---\n")

    lines.append("## Professional Experience\n")
    results = {}

    for role in ROLE_HEADINGS:
        role_clean = normalize_role_name(role)
        baseline_bullets = baselines.get(role_clean, [])

        openai_bullets = safe_openai_request(role, job_title, company_name)
        bullets, mode = normalize_bullets(openai_bullets, baseline_bullets)
        results[role] = {"mode": mode, "count": len(bullets)}

        if "Independent Data Analyst" in role:
            date_line = "**Jan 2025 – Present | Greater Toronto Area, Canada**"
        elif "PepsiCo" in role:
            date_line = "**Mar 2020 – Jan 2025 | Mississauga, ON**"
        elif "MPAC" in role:
            date_line = "**Aug 2003 – Mar 2020 | Pickering, ON**"
        else:
            date_line = ""

        lines.append(f"### {role}\n")
        if date_line:
            lines.append(f"{date_line}\n")
        for b in bullets:
            lines.append(f"- {b}\n")
        lines.append("\n")

    lines.append("---\n")
    lines.append("## Education & Certifications\n")
    lines.append("- BrainStation - Data Science Certification (2025)\n")
    lines.append("- Dalhousie University - BA in Economics\n")
    lines.append("- ITI Halifax - Applied Information Technology Diploma\n")
    lines.append("- Toronto Metropolitan University - Business Administration Certificate\n")
    lines.append("- UiPath RPA Developer Foundation\n")
    lines.append("- SAS Certified Base Programmer\n")
    lines.append("- University of Waterloo - Project Management\n")
    lines.append("- FranklinCovey - The 5 Choices (Time Management)\n")

    return "\n".join(lines), results

def main(jd_path):
    baselines = load_baselines()
    company_name, job_title, closing_date, jd_url = parse_jd(jd_path)
    if not company_name:
        raise ValueError(f"No company found in {jd_path}")

    company_clean = re.sub(r"[^A-Za-z0-9]", "", company_name)

    outputs_dir = Path(jd_path).parent.parent / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    out_file = outputs_dir / f"Gamal_Mensah_Resume_{company_clean}.md"
    resume_md, role_data = build_resume(company_name, job_title, closing_date, jd_url, baselines)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(resume_md)

    result_file = outputs_dir / "result.json"
    ats_data = {
        "company": company_name,
        "job_title": job_title,
        "closing_date": closing_date,
        "jd_path": str(jd_path),
        "jd_url": jd_url,
        "resume_file": os.path.basename(out_file),
        "roles": role_data
    }
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(ats_data, f, indent=2)

    print(f"[INFO] Resume saved to {out_file}")
    print(f"[INFO] ATS data saved to {result_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_resume_from_jd.py <jd_path>")
        sys.exit(1)
    main(sys.argv[1])
