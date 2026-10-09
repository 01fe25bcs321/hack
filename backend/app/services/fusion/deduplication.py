import re
from difflib import SequenceMatcher

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()

def deterministic_duplicates(claims: list[dict], threshold: float = 0.84) -> list[dict]:
    groups = []
    used = set()
    for i, a in enumerate(claims):
        if i in used:
            continue
        group = [a]
        for j in range(i + 1, len(claims)):
            if j in used:
                continue
            if similarity(a["claim"], claims[j]["claim"]) >= threshold:
                group.append(claims[j])
                used.add(j)
        if len(group) > 1:
            used.add(i)
            groups.append({"claims": [x["claim"] for x in group], "sources": sorted({s for x in group for s in x.get("sources", [])}), "reason": "High textual similarity"})
    return groups
