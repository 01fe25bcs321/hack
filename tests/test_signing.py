from backend.app.services.crypto.signing import SigningService

def test_sign_and_verify(tmp_path):
    s=SigningService(str(tmp_path));data=b'hello';sig=s.sign(data);assert s.verify(data,sig);assert not s.verify(b'changed',sig)
