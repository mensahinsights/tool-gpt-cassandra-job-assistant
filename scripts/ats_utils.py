#!/usr/bin/env python3
import re

def tokenize(text: str):
    return re.findall(r"\b\w+\b", text.lower())

def compute_ats_score(jd_text: str, skills_file: str) -> float:
    with open(skills_file, "r", encoding="utf-8") as f:
        skills = [line.strip().lower() for line in f if line.strip()]
    jd_tokens = set(tokenize(jd_text))
    matched = [s for s in skills if s in jd_tokens]
    return round(len(matched) / len(skills) * 100, 2) if skills else 0.0
