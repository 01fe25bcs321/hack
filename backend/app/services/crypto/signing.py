from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat

class SigningService:
    def __init__(self, key_dir: str):
        self.key_dir = Path(key_dir)
        self.private_path = self.key_dir / "private_key.pem"
        self.public_path = self.key_dir / "public_key.pem"
        self.key_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_keys()

    def _ensure_keys(self):
        if self.private_path.exists() and self.public_path.exists():
            return
        private = Ed25519PrivateKey.generate()
        self.private_path.write_bytes(private.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        self.public_path.write_bytes(private.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
        try:
            self.private_path.chmod(0o600)
        except OSError:
            pass

    def _private(self):
        return serialization.load_pem_private_key(self.private_path.read_bytes(), password=None)

    def public_key_pem(self) -> str:
        return self.public_path.read_text(encoding="utf-8")

    def sign(self, data: bytes) -> str:
        import base64
        return base64.b64encode(self._private().sign(data)).decode("ascii")

    def verify(self, data: bytes, signature_b64: str, public_key_pem: str | None = None) -> bool:
        import base64
        try:
            public = serialization.load_pem_public_key((public_key_pem or self.public_path.read_text(encoding="utf-8")).encode())
            public.verify(base64.b64decode(signature_b64), data)
            return True
        except Exception:
            return False
