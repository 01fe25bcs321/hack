SYSTEM_PROMPT = """You are an evidence-based document reconciliation engine.
Use ONLY the supplied source data. Never invent, infer, or silently resolve facts.
Return JSON matching the requested schema.
Classify claims as VERIFIED, CONFLICT, DUPLICATE, UNSUPPORTED, or UNCERTAIN.
Every claim must reference source IDs. Every date/number/entity must reference evidence where possible.
If there are no conflicts, return an empty conflicts list. If there are no important dates, return an empty important_dates list.
The executive summary and AI assessment must distinguish evidence from uncertainty. Provide 0-5 cautious predictions only when source evidence supports them. Predictions must be clearly labeled as estimates, include source-backed basis, confidence (High|Medium|Low), and caveats. Never present a prediction as a verified fact. If evidence is insufficient, return an empty predictions list.
"""

def build_prompt(sources: list[dict]) -> str:
    import json
    schema = {
      "summary":"string", "key_points":["string"],
      "claims":[{"claim":"string","sources":["source_id"],"confidence":0.0,"claim_type":"fact","evidence":["text"],"classification":"VERIFIED|CONFLICT|DUPLICATE|UNSUPPORTED|UNCERTAIN"}],
      "entities":[{"type":"string","value":"string","sources":["source_id"]}],
      "important_dates":[{"value":"string","context":"string","sources":["source_id"]}],
      "important_numbers":[{"value":"string","context":"string","sources":["source_id"]}],
      "duplicates":[{"claims":["string"],"sources":["source_id"],"reason":"string","classification":"DUPLICATE"}],
      "conflicts":[{"field":"string","values":[{"value":"string","source":"source_id"}],"status":"UNRESOLVED","reason":"string","classification":"CONFLICT"}],
      "missing_information":["string"], "source_evidence":[{"claim":"string","source_id":"string","evidence":"string","confidence":"High|Medium|Low"}], "ai_assessment":"string", "predictions":[{"prediction":"string","basis":["source-backed reason"],"confidence":"High|Medium|Low","caveats":["uncertainty"]}], "ai_status":"COMPLETED"
    }
    return SYSTEM_PROMPT + "\nOUTPUT SCHEMA:\n" + json.dumps(schema) + "\nSOURCE DATA:\n" + json.dumps(sources, ensure_ascii=False, indent=2)
