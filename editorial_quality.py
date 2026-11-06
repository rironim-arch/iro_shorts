"""Editorial preflight for 생활알고리즘. Does not certify facts or YouTube eligibility."""
import json, re, sys
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlparse
from datetime import datetime
from zoneinfo import ZoneInfo

TOPICS=Path("editorial_topics.json")
OUT=Path("output_editorial")
OUT.mkdir(exist_ok=True)
FORMATS={"warning","myth","checklist","comparison"}
REQUIRED={"id","category","format","title","scripts","fact","source_name","source_url","source_checked_on","audience_action","visuals"}
VAGUE_PHRASES=["무조건 100%","기적의","충격 실화","의사도 모르는","딱 하나로 완치"]

def normalize(s):
    return re.sub(r"[\W_]+","",s.lower())

def audit(topics):
    faults=[]
    ids=[]
    for topic in topics:
        tid=topic.get("id")
        ids.append(tid)
        prefix=f"topic {tid}"
        missing=REQUIRED-set(topic)
        if missing:
            faults.append(f"{prefix}: missing {', '.join(sorted(missing))}")
            continue
        if topic["format"] not in FORMATS:
            faults.append(f"{prefix}: unknown visual format")
        lines=topic["scripts"]
        if not isinstance(lines,list) or not 5<=len(lines)<=8:
            faults.append(f"{prefix}: script needs 5 to 8 complete lines")
            continue
        if len(topic["visuals"])!=len(lines):
            faults.append(f"{prefix}: each narrated line must have its own visual plan")
        raw=" ".join(lines)
        if not 145<=len(normalize(raw))<=480:
            faults.append(f"{prefix}: insufficient or overly long educational detail")
        if any(len(ln)>105 for ln in lines):
            faults.append(f"{prefix}: narration line exceeds 105 characters")
        if len(set(map(normalize,lines)))!=len(lines):
            faults.append(f"{prefix}: repeated sentence inside the same script")
        if not (9<=len(topic["title"])<=55):
            faults.append(f"{prefix}: title length needs review")
        if any(p in raw for p in VAGUE_PHRASES):
            faults.append(f"{prefix}: ungrounded sensational claim")
        url=urlparse(topic["source_url"])
        if url.scheme!="https" or not url.netloc:
            faults.append(f"{prefix}: factual source must be an HTTPS citation")
        if not topic["fact"].strip() or len(topic["fact"])<15:
            faults.append(f"{prefix}: key fact must be stated")
        if not topic["audience_action"].strip():
            faults.append(f"{prefix}: actionable guidance required")
        if lines[0].strip()!=topic.get("hook",lines[0]).strip():
            faults.append(f"{prefix}: hook differs from first spoken line")
    if len(ids)!=len(set(ids)):
        faults.append("Duplicate topic IDs")
    for i,a in enumerate(topics):
        for b in topics[i+1:]:
            if "scripts" not in a or "scripts" not in b:
                continue
            aa=normalize(" ".join(a["scripts"]))
            bb=normalize(" ".join(b["scripts"]))
            ratio=SequenceMatcher(None,aa,bb).ratio()
            if ratio>0.69:
                faults.append(f"Topics {a['id']} / {b['id']} too similar ({ratio:.2f})")
            if normalize(a["scripts"][0])==normalize(b["scripts"][0]):
                faults.append(f"Topics {a['id']} / {b['id']} have identical hooks")
            if normalize(a["scripts"][-1])==normalize(b["scripts"][-1]):
                faults.append(f"Topics {a['id']} / {b['id']} have identical endings")
    return faults

def run_review():
    topics=json.loads(TOPICS.read_text(encoding="utf-8"))
    errors=audit(topics)
    report={
        "checked_at_kst":datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        "topic_count":len(topics),
        "syntactic_checks_passed":len(errors)==0,
        "errors":errors,
        "manual_fact_check_required":True,
        "manual_footage_rights_check_required":True,
        "manual_Youtube_policy_review_required":True,
        "automated_publish_enabled":False,
        "disclaimer":"Automated checks cannot establish factual accuracy, originality, copyright clearance or YouTube monetization eligibility."
    }
    (OUT/"quality_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    if errors:raise SystemExit(2)
    return topics

if __name__=="__main__":
    run_review()
