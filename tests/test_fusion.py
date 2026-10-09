from backend.app.services.fusion.deduplication import deterministic_duplicates

def test_duplicate_detection():
    claims=[{'claim':'Project Alpha finished in March 2026','sources':['SRC-001']},{'claim':'Project Alpha was finished in March 2026','sources':['SRC-002']}]
    assert deterministic_duplicates(claims)
