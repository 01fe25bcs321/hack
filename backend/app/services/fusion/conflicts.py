import re

def _amounts(text: str):
    return re.findall(r"(?:₹|INR|Rs\.?|USD|\$)\s?[\d,]+(?:\.\d+)?", text, flags=re.I)

def deterministic_conflicts(sources: list[dict]) -> list[dict]:
    budget = []
    for s in sources:
        for line in s.get("claims", []):
            if re.search(r"\bbudget\b", line, re.I):
                vals = _amounts(line)
                if vals:
                    budget.append((s["source_id"], vals[0], line))
    unique = {(sid, val) for sid, val, _ in budget}
    values = {val for _, val, _ in budget}
    if len(values) > 1:
        conflicts = []
        for i in range(len(budget)):
            for j in range(i + 1, len(budget)):
                if budget[i][1] != budget[j][1]:
                    conflicts.append({"field": "budget", "values": [{"value": budget[i][1], "source": budget[i][0]}, {"value": budget[j][1], "source": budget[j][0]}], "status": "unresolved", "reason": "Different budget values found in separate sources."})
        return conflicts
    return []
