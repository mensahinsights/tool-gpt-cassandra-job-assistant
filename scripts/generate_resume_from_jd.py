#!/usr/bin/env python3
import os, sys, json, traceback
from datetime import datetime
from scripts.ats_utils import compute_ats_score
from scripts.resume_utils import load_baseline, render_resume


def parse_jd(jd_path: str):
    with open(jd_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) < 3:
        raise ValueError("JD must have at least 3 header lines (Company, Job Title, Closing Date).")
    company = lines[0].split(":", 1)[-1].strip()
    title = lines[1].split(":", 1)[-1].strip()
    closing = lines[2].split(":", 1)[-1].strip()
    jd_text = "".join(lines[3:])
    return company, title, closing, jd_text


def safe_write_result(data: dict, path: str = "result.json"):
    """Always write a JSON file, even on error."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[DEBUG] Wrote result.json: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"[ERROR] Failed to write result.json: {e}")


def main():
    if len(sys.argv) != 2:
        err = {"status": "error", "message": "Usage: generate_resume_from_jd.py <jd.md>"}
        safe_write_result(err)
        sys.exit(1)

    jd_path = sys.argv[1]
    print(f"[DEBUG] Reading JD file: {jd_path}")

    try:
        company, title, closing, jd_text = parse_jd(jd_path)
        print(f"[DEBUG] Parsed JD header -> Company: {company}, Job Title: {title}, Closing Date: {closing}")

        # Compute ATS Score
        ats_score = compute_ats_score(jd_text, "data/skills.txt")
        print(f"[DEBUG] Computed ATS Score: {ats_score}%")

        # Load baseline resume
        baseline = load_baseline()
        print(f"[DEBUG] Loaded baseline resume with {len(baseline['experience'])} experience entries.")

        # Tailoring context
        tailoring = {
            "headline": f"{title} who drives outcomes at {company}",
            "summary": baseline["summary"] + f" Tailored for {company}, closing {closing}.",
            "ats_score": ats_score
        }

        # Output path
        job_folder = os.path.dirname(os.path.dirname(jd_path))
        outputs_dir = os.path.join(job_folder, "outputs")
        print(f"[DEBUG] Ensuring outputs directory exists: {outputs_dir}")
        os.makedirs(outputs_dir, exist_ok=True)

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        output_file = os.path.join(
            outputs_dir, f"Mensah_Resume_{company.replace(' ', '')}_v3.1_{date_str}.docx"
        )
        print(f"[DEBUG] Will write resume to: {output_file}")

        # Render resume
        render_resume(output_file, baseline, tailoring)
        print(f"[DEBUG] Resume successfully written: {output_file}")

        # Final result
        result = {
            "status": "success",
            "Date": datetime.utcnow().isoformat(),
            "Company": company,
            "Job_Title": title,
            "JD_Path": jd_path,
            "Closing_Date": closing,
            "ATS_Score": ats_score,
            "Resume_Path": output_file,
        }
        safe_write_result(result)
        sys.exit(0)

    except Exception as e:
        print("[ERROR] Exception occurred while generating resume:")
        traceback.print_exc()

        # Write fallback JSON
        err = {
            "status": "error",
            "message": str(e),
            "jd_path": jd_path,
            "traceback": traceback.format_exc(),
        }
        safe_write_result(err)
        sys.exit(1)


if __name__ == "__main__":
    main()
