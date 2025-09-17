# Cassandra Master Instructions v3.2

## 1) Writing Style and Tone
- Use Canadian spelling conventions (e.g., colour, honour, behaviour, centre).  
- Use “z” endings for verbs (e.g., analyze, organize, realize).  
- Do not use em dashes (—); use commas instead.  
- Maintain a warm, conversational tone that balances professionalism with approachability.  
- Avoid robotic or corporate-sounding phrasing. Content must read as though a knowledgeable colleague wrote it.  

## 2) Resume Output
- All resumes must be produced in `.docx` format.  
- File naming convention: `Gamal_Mensah_Resume_<CompanyName>.docx`  
  - Example: `Gamal_Mensah_Resume_Lactalis.docx`  
- No ATS scores are to be embedded in the resume itself.  

## 3) Input Expectations
- Job descriptions are stored in `runs/<date>_<company_role>/inputs/jd.md`.  
- `jd.md` may contain:  
  - Company  
  - Job Title  
  - Closing Date (optional)  
  - URL (optional)  
- Workflow automatically parses these values.  

## 4) Resume Generation Workflow
- Workflow triggers when a `jd.md` file is added or updated.  
- The script processes the JD, parses company, title, closing date, and URL.  
- A resume is generated from the base template and saved under `runs/.../outputs/`.  
- Metadata is written to `result.json`.  

## 5) Environment
- Python 3.11 is used in GitHub Actions.  
- Dependencies are pinned in `requirements.txt`.  
- OpenAI API key is stored in repo secrets as `OPENAI_API_KEY`.  
- Google Sheets integration requires `GOOGLE_SHEETS_CREDENTIALS` and `SHEET_ID`.  

## 6) Baseline Bullets
- **[UPDATED]** Baseline bullets are no longer stored in the Word template.  
- They are now stored in `scripts/baselines.json`.  
- Each role has a set of 4–6 default bullets that reflect authentic prior contributions.  
- These serve as fallbacks if OpenAI cannot generate sufficient tailored bullets.  

## 7) Resume Structure and Role Bullets
- **[UPDATED]** `resume_template.docx` must contain only:  
  - Section headings (e.g., role titles, Education & Certifications).  
  - No pre-filled bullets under roles.  
- During generation, the script clears any existing bullets and replaces them entirely.  
- For each role:  
  1. OpenAI generates tailored bullets aligned with the JD.  
  2. Always enforce **minimum 4, maximum 6 bullets**.  
  3. If OpenAI returns fewer than 4, baseline bullets are drawn from `baselines.json` until the minimum is met.  
  4. If OpenAI fails entirely, baseline bullets fill the role completely.  
  5. If OpenAI produces more than 6, extra bullets are truncated.  
- **Result:** Every role will always contain 4–6 clean, JD-aligned bullets with no placeholders or duplicates.  

## 8) Google Sheets Output
- Metadata in `result.json` includes:  
  - Company  
  - Job Title  
  - Closing Date (if provided, else TBD Closing Date)  
  - JD Path  
  - JD URL (if provided)  
  - Resume File Name  
  - Roles with bullet metadata (mode, bullet count, insertion index).  
- This data is uploaded to Google Sheets for tracking.  

## 9) Error Handling
- If OpenAI API is unavailable, script logs a warning and falls back to baseline bullets.  
- If template is missing, job fails with explicit error.  
- If no company name is found in JD, job fails with explicit error.  

## 10) File Conventions
- Template: `templates/resume_template.docx`  
- Baselines: `scripts/baselines.json`  
- Script: `scripts/generate_resume_from_jd.py`  
- Workflow: `.github/workflows/generate_resume.yml`  

---

# Appendix A: Managing Baseline Bullets

- **File:** `scripts/baselines.json`  
- **Purpose:** Provides authentic fallback bullets for each role in case OpenAI generates too few or no tailored bullets.  
- **Format:** JSON object, with role titles as keys and an array of bullet strings as values.  

### Example
```json
{
  "Independent Data Analyst | BI & Automation Consultant": [
    "Automated reporting pipelines that saved 10+ hours weekly across client teams.",
    "Built custom Power BI dashboards and SQL queries to improve decision-making speed by 30%.",
    "Developed Python scripts to streamline data cleansing and reconciliation processes.",
    "Implemented RPA workflows with UiPath to eliminate repetitive manual tasks."
  ],
  "Senior Transformation Analyst | PepsiCo": [
    "Raised Precision Ordering compliance from 69% to 95% by integrating dashboards, automation, and field team coaching.",
    "Designed KPI dashboards that provided real-time visibility into sales, supply chain, and execution metrics.",
    "Partnered with cross-functional teams to identify root causes of compliance gaps and drive corrective action.",
    "Supported business transformation initiatives by analyzing large datasets and producing actionable insights."
  ]
}
