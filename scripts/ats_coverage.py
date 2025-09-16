#!/usr/bin/env python3
import sys, re, pathlib, json

STOP = set("""a an the and or but if to of in for on at as by from with is are was were be been being this that those these it its into within over under between across per""".split())

def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]+", " ", text)
    toks = [t for t in text.split() if t and t not in STOP]
    return toks

def ngrams(tokens, n=2):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def extract_terms(jd_text):
    toks = tokenize(jd_text)
    uni = set(toks)
    bi = set(ngrams(toks, 2))
    uni = {t for t in uni if len(t) > 2}
    return uni, bi

def coverage(jd_uni, jd_bi, resume_text):
    toks = tokenize(resume_text)
    uni = set(toks)
    bi = set(ngrams(toks, 2))
    must = jd_uni | jd_bi
    target = list(sorted(must))[:200]
    present = [t for t in target if (t in uni) or (t in bi)]
    pct = round(100.0 * len(present) / max(1, len(target)), 1)
    missing = [t for t in target if t not in present]
    return pct, present, missing

def main(jd_path, resume_path):
    jd = pathlib.Path(jd_path).read_text(encoding="utf-8")
    res = pathlib.Path(resume_path).read_text(encoding="utf-8")
    jd_uni, jd_bi = extract_terms(jd)
    pct, present, missing = coverage(jd_uni, jd_bi, res)
    report = {
        "coverage_percent": pct,
        "present_terms": present[:50],
        "missing_terms": missing[:50]
    }
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ats_coverage.py <JD.md> <resume.md>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
