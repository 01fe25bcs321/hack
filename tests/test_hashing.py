from backend.app.services.crypto.hashing import canonicalize, canonical_hash

def test_canonical_hash_deterministic():
    a={'b':2,'a':1};b={'a':1,'b':2};assert canonicalize(a)==canonicalize(b);assert canonical_hash(a)==canonical_hash(b)
