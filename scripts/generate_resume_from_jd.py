import os
import sys
import json
import re
from pathlib import Path
from openai import OpenAI

# --------------------------
# Config
# --------------------------
MODEL = "gpt-4o-mini"
BASELINES_PATH = "baselines.json"

# --------------------------
# Utilities
# --------------------------
def normalize_text(text: str) -> str:
    """Ensure ASCII-only: replace dashes, normalize quotes, trim whitespace."""
    text = text.replace("\u2014", "-")  # em dash
    text = text.replace("\u2013", "-")  # en dash
    text = text.replace("\u201C", "\"").replace("\u201D", "\"")  # curly double quotes
    text = text.replace("\u2018", "'").replace("\u2019", "'")   # curly single quotes
    text = text.replace("\u2022", "-")  # bullet
    return text.strip()

def load_baselines() -> dict:
    with open(BASELINES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_jd_header(jd_path: Path) -> dict:
    """Extract Company, Job Title, Closing Date, URL from JD header."""
    header = {"company": "Unknown", "job_title": "Unknown", "closing_date": "TBD", "jd_url": ""}
    with open(jd_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("Company:"):
            header["company"] = normalize_text(line.split(":", 1)[1].strip())
        elif line.startswith("Job Title:"):
            header["job_title"] = normalize_text(line.split(":", 1)[1].strip())
        elif line.startswith("Closing Date:"):
            header["closing_date"] = normalize_text(line.split(":", 1)[1].strip()) or "TBD"
        elif line.startswith("URL:"):
            header["jd_url"] = normalize_text(line.split(":", 1)[1].strip())
        if line.strip() == "":
            break
    return header

def generate_ai_bullets(role: str, job_title: str, company: str, baseline: list) -> list:
    """Ask OpenAI to tailor bullets for a role; fallback gracefully."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []

    try:
        client = OpenAI(api_key=api_key)
        prompt = (
            f"Tailor 4-6 resume bullets for the role '{role}' so they align with the job title '{job_title}' "
            f"at company '{company}'. Use action verbs, quantify impact where possible, avoid placeholders."
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert resume writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.7,
        )

        raw = response.choices[0].message.content.strip()
        bullets = [normalize_text(line) for line in raw.split("\n") if line.strip()]
        bullets = [re.sub(r"^[\-\*\u2022]\s*", "", b) for b in bullets]
        return bullets
    except Exception as e:
        print(f"[DEBUG] OpenAI request failed for {role}: {e}")
        return []

from typing import List, Tuple
def enforce_bullet_count(bullets: List[str], baseline: List[str]) -> Tuple[List[str], str]:
    """Guarantee 4-6 bullets. Use baseline or defaults if AI fails."""
    defaults = [
        "Analyzed data to support decision-making.",
        "Collaborated with teams to improve processes.",
        "Developed reports to monitor key metrics.",
        "Streamlined workflows to increase efficiency."
    ]

    mode = "AI"

    if not bullets:
        bullets = baseline if baseline else defaults
        mode = "Baseline" if baseline else "Default"

    if len(bullets) < 4:
        bullets += (baseline if baseline else defaults)
        bullets = bullets[:4]
        mode += "+Padded"
    elif len(bullets) > 6:
        bullets = bullets[:6]

    return bullets, mode

def build_resume(jd_path: Path, baselines: dict):
    jd_meta = parse_jd_header(jd_path)
    company, job_title = jd_meta["company"], jd_meta["job_title"]

    out_dir = jd_path.parent.parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    resume_filename = f"Gamal_Mensah_Resume_{company.replace(' ', '')}.md"
    resume_path = out_dir / resume_filename
    result_path = out_dir / "result.json"

    sections = []
    roles_processed = {}   # ✅ always initialized

    try:
        if "Contact" in baselines:
            sections.append(f"# Gamal Mensah Resume\n\n{baselines['Contact']}")

        if "Summary" in baselines:
            summary_text = " ".join([normalize_text(s) for s in baselines["Summary"]])
            sections.append(f"## Summary\n{summary_text}")

        work_lines = ["## Work Experience"]

        for role, baseline_bullets in baselines.items():
            if role in ["Contact", "Summary", "Education", "Skills"]:
                continue

            ai_bullets = generate_ai_bullets(role, job_title, company, baseline_bullets)
            bullets, mode = enforce_bullet_count(ai_bullets, baseline_bullets)

            work_lines.append(f"### {role}")
            for b in bullets:
                work_lines.append(f"- {b}")

            print(f"[DEBUG] Role: {role} -> {mode} ({len(bullets)} bullets)")
            roles_processed[role] = {"mode": mode, "bullet_count": len(bullets)}

        sections.append("\n".join(work_lines))

        if "Education" in baselines:
            edu_lines = ["## Education"] + [f"- {normalize_text(e)}" for e in baselines["Education"]]
            sections.append("\n".join(edu_lines))

        if "Skills" in baselines:
            skill_lines = ["## Skills"] + [f"- {normalize_text(s)}" for s in baselines["Skills"]]
            sections.append("\n".join(skill_lines))

        result = {
            "company": company,
            "job_title": job_title,
            "closing_date": jd_meta["closing_date"],
            "jd_url": jd_meta["jd_url"],
            "roles_processed": roles_processed,
        }

    except Exception as e:
        print(f"[ERROR] Failed during resume build: {e}")
        # ✅ still create a minimal result.json so downstream steps don't break
        result = {
            "company": company,
            "job_title": job_title,
            "closing_date": jd_meta.get("closing_date", "TBD"),
            "jd_url": jd_meta.get("jd_url", ""),
            "roles_processed": roles_processed,
            "error": str(e),
        }

    # ✅ Always write resume + result.json
    with open(resume_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(sections))

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[DEBUG] Workflow completed successfully, resume saved to {resume_path}")
    return resume_path, result_path

def main(jd_path: str):
    baselines = load_baselines()
    build_resume(Path(jd_path), baselines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_resume_from_jd.py <jd.md>")
        sys.exit(1)
    main(sys.argv[1])
