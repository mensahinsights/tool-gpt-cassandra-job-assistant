import os
import json
import yaml
from pathlib import Path
from docx import Document

# Assume you already have a function that parses jd.md
def parse_jd(jd_path):
    company = None
    job_title = None
    with open(jd_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.lower().startswith("company:"):
                company = line.split(":", 1)[1].strip()
            if line.lower().startswith("job title:"):
                job_title = line.split(":", 1)[1].strip()
    return company, job_title

# Stub: replace with your actual resume generator logic
def generate_resume(company_name, job_title):
    doc = Document()
    doc.add_heading("Gamal Mensah – Resume", 0)
    doc.add_paragraph(f"Target Company: {company_name}")
    doc.add_paragraph(f"Target Role: {job_title}")
    doc.add_paragraph("Professional summary and experience go here...")
    # >>> DO NOT include ATS score in resume content <<<
    return doc

def main(jd_path):
    company_name, job_title = parse_jd(jd_path)
    if not company_name:
        raise ValueError(f"No company found in {jd_path}")

    # Clean company name for filename (remove spaces/symbols)
    company_clean = (
        company_name.replace(" ", "")
        .replace("&", "")
        .replace(",", "")
        .replace(".", "")
    )

    # Create outputs folder if missing
    outputs_dir = Path(jd_path).parent.parent / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Save resume as Gamal_Mensah_Resume_<Company>.docx
    out_file = outputs_dir / f"Gamal_Mensah_Resume_{company_clean}.docx"
    resume = generate_resume(company_name, job_title)
    resume.save(out_file)

    # Example ATS scoring (optional – just stored, not written into docx)
    ats_score = 85  # Replace with real scoring function if you have one
    ats_data = {
        "company": company_name,
        "job_title": job_title,
        "ats_score": ats_score,
        "resume_file": str(out_file)
    }

    # Save result.json for Sheets update step
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
