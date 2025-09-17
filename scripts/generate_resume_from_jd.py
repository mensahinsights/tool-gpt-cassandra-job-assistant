import os
import json
from pathlib import Path
from docx import Document

try:
    import openai
except ImportError:
    openai = None

def parse_jd(jd_path):
    """Extract company and job title from jd.md"""
    company = None
    job_title = None
    with open(jd_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.lower().startswith("company:"):
                company = line.split(":", 1)[1].strip()
            if line.lower().startswith("job title:"):
                job_title = line.split(":", 1)[1].strip()
    return company, job_title

def generate_bullet_points(job_title, company_name):
    """Generate tailored bullet points using OpenAI if key is set, otherwise fallback"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not openai:
        print("[WARN] OpenAI not available, using static fallback bullets.")
        return [
            "Delivered measurable improvements to data reporting accuracy.",
            "Partnered with business teams to define KPIs and reporting standards.",
            "Implemented dashboards that reduced analysis time by 50%."
        ], "fallback"

    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert resume writer."},
                {"role": "user", "content": f"Generate 3 strong resume bullet points tailored for a {job_title} role at {company_name}. Focus on measurable business impact, analytics, and problem-solving. Return only bullet points."}
            ]
        )
        bullets = response.choices[0].message["content"].split("\n")
        clean_bullets = [b.strip("-• ") for b in bullets if b.strip()]
        return clean_bullets, "openai"
    except Exception as e:
        print(f"[WARN] OpenAI request failed: {e}")
        return [
            "Delivered measurable improvements to data reporting accuracy.",
            "Partnered with business teams to define KPIs and reporting standards.",
            "Implemented dashboards that reduced analysis time by 50%."
        ], "fallback"

def generate_resume(company_name, job_title):
    """Build the resume .docx"""
    bullets, mode = generate_bullet_points(job_title, company_name)

    doc = Document()
    doc.add_heading("Gamal Mensah – Resume", 0)
    doc.add_paragraph(f"Target Company: {company_name}")
    doc.add_paragraph(f"Target Role: {job_title}")

    doc.add_heading("Key Achievements", level=1)
    for bullet in bullets:
        doc.add_paragraph(bullet, style="List Bullet")

    return doc, mode, bullets

def main(jd_path):
    company_name, job_title = parse_jd(jd_path)
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
    resume, mode, bullets = generate_resume(company_name, job_title)
    resume.save(out_file)

    ats_score = 85  # Replace with real scoring logic if needed
    ats_data = {
        "company": company_name,
        "job_title": job_title,
        "ats_score": ats_score,
        "resume_file": os.path.basename(str(out_file)),
        "bullet_mode": mode,
        "bullets": bullets
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
