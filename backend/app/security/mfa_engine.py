import pyotp

class MFAEngine:
    """
    Handles Multi-Factor Authentication via TOTP.
    """
    
    def generate_secret(self) -> str:
        """Generates a base32 secret for TOTP."""
        return pyotp.random_base32()
        
    def get_provisioning_uri(self, secret: str, email: str, issuer_name: str = "claimOS") -> str:
        """Generates the URI for QR Code generation (Google Authenticator)."""
        return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer_name)
        
    def verify_totp(self, secret: str, code: str) -> bool:
        """Verifies the TOTP code against the user's secret."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
        
mfa_engine = MFAEngine()
