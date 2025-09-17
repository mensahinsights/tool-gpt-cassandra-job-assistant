import os
import json
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

try:
    import openai
except ImportError:
    openai = None

# Path to resume template
TEMPLATE_PATH = Path("templates/resume_template.docx")

# Roles expected in the template
ROLE_HEADINGS = [
    "Independent Data Analyst | BI & Automation Consultant",
    "Senior Transformation Analyst | PepsiCo",
    "IT Analyst | MPAC"
]


def parse_jd(jd_path):
    """Extract Company, Job Title, Closing Date, and URL from jd.md"""
    company, job_title = None, None
    closing_date, jd_url = "TBD Closing Date", ""
    with open(jd_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.lower().startswith("company:"):
                company = line.split(":", 1)[1].strip()
            elif line.lower().startswith("job title:"):
                job_title = line.split(":", 1)[1].strip()
            elif line.lower().startswith("closing date:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    closing_date = value
            elif line.lower().startswith("url:"):
                jd_url = line.split(":", 1)[1].strip()
    return company, job_title, closing_date, jd_url


def generate_bullets_for_role(role_title, job_title, company_name):
    """
    Generate tailored bullets for a given role using OpenAI if available.
    Fallback: safe highlight bullet.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not openai:
        return [f"Highlighted achievements from {role_title}."], "fallback"

    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert resume writer."},
                {"role": "user", "content": (
                    f"Given the past role '{role_title}' and the target role '{job_title}' at {company_name}, "
                    "generate up to 3 resume bullet points showing alignment. "
                    "If no JD-relevance exists, return highlights from the role without inventing new responsibilities. "
                    "Return only bullet points."
                )}
            ]
        )
        bullets = response.choices[0].message["content"].split("\n")
        clean_bullets = [b.strip("-• ") for b in bullets if b.strip()]
        if not clean_bullets:
            return [f"Highlighted achievements from {role_title}."], "fallback"
        return clean_bullets, "openai"
    except Exception as e:
        print(f"[WARN] OpenAI request failed for {role_title}: {e}")
        return [f"Highlighted achievements from {role_title}."], "fallback"


def insert_paragraph_after(paragraph, text, style=None):
    """Helper: Insert a new paragraph directly after a given one."""
    new_p = OxmlElement("w:p")
    paragraph._element.addnext(new_p)
    new_para = paragraph._parent.add_paragraph(text, style=style)
    new_p.addnext(new_para._element)
    return new_para


def embed_bullets(doc, job_title, company_name):
    """
    Insert tailored bullets under each role heading,
    before the next role heading or Education section.
    Returns dict: {role: {"mode": "...", "bullets": [...]}, ...}
    """
    results = {}

    for role in ROLE_HEADINGS:
        role_para = None
        for para in doc.paragraphs:
            if role in para.text:
                role_para = para
                break

        if not role_para:
            print(f"[WARN] Role heading '{role}' not found.")
            continue

        # Find where to insert bullets (after last existing bullet for this role)
        insert_after = role_para
        for para in doc.paragraphs[doc.paragraphs.index(role_para) + 1:]:
            if any(r in para.text for r in ROLE_HEADINGS if r != role) or "Education & Certifications" in para.text:
                break
            if para.style and para.style.name.startswith("List Bullet"):
                insert_after = para

        # Generate bullets
        bullets, mode = generate_bullets_for_role(role, job_title, company_name)
        results[role] = {"mode": mode, "bullets": bullets}

        # Insert bullets immediately after insert_after
        for bullet in bullets:
            insert_paragraph_after(insert_after, bullet, style="List Bullet")
            insert_after = doc.paragraphs[-1]

        print(f"[INFO] Inserted {len(bullets)} bullets for {role} ({mode})")

    return results


def build_resume(company_name, job_title):
    """Load template and insert tailored bullets for each role"""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")
    doc = Document(TEMPLATE_PATH)
    role_data = embed_bullets(doc, job_title, company_name)
    return doc, role_data


def main(jd_path):
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
    resume, role_data = build_resume(company_name, job_title)
    resume.save(out_file)

    ats_data = {
        "company": company_name,
        "job_title": job_title,
        "closing_date": closing_date,
        "jd_path": str(jd_path),
        "jd_url": jd_url,
        "ats_score": 85,
        "resume_file": os.path.basename(str(out_file)),
        "roles": role_data
    }

    result_file = outputs_dir / "result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(ats_data, f, indent=2)

    print(f"[INFO] Resume saved to {out_file}")
    print(f"[INFO] ATS data saved to {result_file}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_resume_from_jd.py <jd_path>")
        sys.exit(1)
    main(sys.argv[1])
