#!/usr/bin/env python3
import os, sys, json
from datetime import datetime
from scripts.ats_utils import compute_ats_score
from scripts.resume_utils import load_baseline, render_resume

def parse_jd(jd_path: str):
    with open(jd_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) < 3:
        raise ValueError("JD must have at least 3 header lines.")
    company = lines[0].split(":", 1)[-1].strip()
    title = lines[1].split(":", 1)[-1].strip()
    closing = lines[2].split(":", 1)[-1].strip()
    jd_text = "".join(lines[3:])
    return company, title, closing, jd_text

def main():
    if len(sys.argv) != 2:
        print("Usage: generate_resume_from_jd.py <jd.md>")
        sys.exit(1)

    jd_path = sys.argv[1]
    company, title, closing, jd_text = parse_jd(jd_path)

    ats_score = compute_ats_score(jd_text, "data/skills.txt")

    baseline = load_baseline()
    tailoring = {
        "headline": f"{title} who drives outcomes at {company}",
        "summary": baseline["summary"] + f" Tailored for {company}, closing {closing}.",
        "ats_score": ats_score
    }

    job_folder = os.path.dirname(os.path.dirname(jd_path))
    outputs_dir = os.path.join(job_folder, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    output_file = os.path.join(outputs_dir, f"Mensah_Resume_{company.replace(' ','')}_v3.1_{date_str}.docx")

    render_resume(output_file, baseline, tailoring)

    result = {
        "Date": datetime.utcnow().isoformat(),
        "Company": company,
        "Job_Title": title,
        "JD_Path": jd_path,
        "Closing_Date": closing,
        "ATS_Score": ats_score,
        "Resume_Path": output_file
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
