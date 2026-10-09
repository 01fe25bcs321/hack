from backend.app.services.crypto.hashing import canonical_hash
from backend.app.services.crypto.signing import SigningService

def test_tamper_detection(tmp_path):
    s=SigningService(str(tmp_path));doc={'a':1};h=canonical_hash(doc);sig=s.sign(__import__('json').dumps(doc,sort_keys=True,separators=(',',':')).encode());assert s.verify(__import__('json').dumps(doc,sort_keys=True,separators=(',',':')).encode(),sig);doc['a']=2;assert canonical_hash(doc)!=h
