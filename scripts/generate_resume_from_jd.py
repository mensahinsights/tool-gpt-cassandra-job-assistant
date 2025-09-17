import os
import sys
import json
import time
from pathlib import Path
from docx import Document
from docx.shared import Pt
from openai import OpenAI

# Paths
TEMPLATE_PATH = Path("templates/resume_template_cleaned_v2.docx")
BASELINES_PATH = Path("scripts/baselines.json")

ROLE_HEADINGS = [
    "Independent Data Analyst | BI & Automation Consultant",
    "Senior Transformation Analyst | PepsiCo",
    "IT Analyst – R&D and Product Development | MPAC"
]

MIN_BULLETS = 4
MAX_BULLETS = 6


def load_baselines():
    if not BASELINES_PATH.exists():
        raise FileNotFoundError(f"Baseline file not found at {BASELINES_PATH}")
    with open(BASELINES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_jd(jd_path):
    company, job_title = None, None
    closing_date, jd_url = "TBD Closing Date", ""
    with open(jd_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.lower().startswith("company:"):
                company = line.split(":", 1)[1].strip()
            elif line.lower().startswith("job title:"):
                job_title = line.split(":", 1)[1].strip()
            elif line.lower().startswith("closing date:"):
                val = line.split(":", 1)[1].strip()
                if val:
                    closing_date = val
            elif line.lower().startswith("url:"):
                jd_url = line.split(":", 1)[1].strip()
    return company, job_title, closing_date, jd_url


def safe_openai_request(role_title, job_title, company_name):
    """Try OpenAI once, retry once, then fallback"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []

    client = OpenAI(api_key=api_key)

    for attempt in range(2):
        try:
            print(f"[DEBUG] OpenAI request attempt {attempt+1} for {role_title}")
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
            bullets = [b.strip("-• ") for b in content.split("\n") if b.strip()]
            if bullets:
                return bullets
        except Exception as e:
            print(f"[WARN] OpenAI error for {role_title}: {e}")
            time.sleep(2)

    return []


def normalize_bullets(openai_bullets, baseline_bullets):
    bullets, mode = [], "baseline"

    if openai_bullets and MIN_BULLETS <= len(openai_bullets) <= MAX_BULLETS:
        bullets = openai_bullets
        mode = "openai"
    elif baseline_bullets:
        bullets = baseline_bullets[:MAX_BULLETS]
        if len(bullets) < MIN_BULLETS:
            bullets = (bullets * ((MIN_BULLETS // len(bullets)) + 1))[:MIN_BULLETS]
        mode = "baseline"
    else:
        bullets = ["Highlights available upon request."] * MIN_BULLETS
        mode = "filler"

    return bullets, mode


def clear_role_bullets(doc, role_idx):
    """Remove existing bullets for a role so they can be re-inserted cleanly."""
    to_remove = []
    for j in range(role_idx + 1, len(doc.paragraphs)):
        para = doc.paragraphs[j]
        if para.style and para.style.name.startswith("List Bullet"):
            to_remove.append(para)
        if any(r in para.text for r in ROLE_HEADINGS if r != doc.paragraphs[role_idx].text) \
           or "Education & Certifications" in para.text:
            break
    for p in to_remove:
        p._element.getparent().remove(p._element)


def embed_bullets(doc, job_title, company_name, baselines):
    results = {}
    for role in ROLE_HEADINGS:
        role_idx = None
        for i, para in enumerate(doc.paragraphs):
            if role in para.text:
                role_idx = i
                break
        if role_idx is None:
            print(f"[WARN] Role heading '{role}' not found.")
            continue

        clear_role_bullets(doc, role_idx)
        date_para = doc.paragraphs[role_idx + 1]

        openai_bullets = safe_openai_request(role, job_title, company_name)
        baseline_bullets = baselines.get(role, [])
        bullets, mode = normalize_bullets(openai_bullets, baseline_bullets)

        results[role] = {"mode": mode, "count": len(bullets)}

        insert_after = date_para
        for b in bullets:
            new_para = insert_after.insert_paragraph_before(b, style="List Bullet")
            new_para.paragraph_format.space_after = Pt(0)
            new_para.paragraph_format.space_before = Pt(0)
            insert_after = new_para

        print(f"[INFO] Inserted {len(bullets)} bullets for {role} ({mode})")

    return results


def build_resume(company_name, job_title, baselines):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")
    doc = Document(TEMPLATE_PATH)
    role_data = embed_bullets(doc, job_title, company_name, baselines)
    return doc, role_data


def main(jd_path):
    baselines = load_baselines()
    company_name, job_title, closing_date, jd_url = parse_jd(jd_path)
    if not company_name:
        raise ValueError(f"No company found in {jd_path}")

    company_clean = (
        company_name.replace(" ", "")
        .replace("&", "")
        .replace(",", "")
        .replace(".", "")
    )

    outputs_dir = Path(jd_path).parent.parent / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    out_file = outputs_dir / f"Gamal_Mensah_Resume_{company_clean}.docx"
    resume, role_data = build_resume(company_name, job_title, baselines)
    resume.save(out_file)

    ats_data = {
        "company": company_name,
        "job_title": job_title,
        "closing_date": closing_date,
        "jd_path": str(jd_path),
        "jd_url": jd_url,
        "resume_file": os.path.basename(str(out_file)),
        "roles": role_data,
    }

    result_file = outputs_dir / "result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(ats_data, f, indent=2)

    print(f"[INFO] Resume saved to {out_file}")
    print(f"[INFO] ATS data saved to {result_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_resume_from_jd.py <jd_path>")
        sys.exit(1)
    main(sys.argv[1])
