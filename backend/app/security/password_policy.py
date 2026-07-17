from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class PasswordPolicyManager:
    """
    Enforces password complexity, hashes passwords, and verifies them.
    """
    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_number = True
        self.require_special = True
        
        # Simple brute force tracking mock (IP or Username based)
        self.failed_attempts = {}
        self.lockout_threshold = 5

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def is_complex_enough(self, password: str) -> bool:
        if len(password) < self.min_length:
            return False
        if self.require_uppercase and not any(c.isupper() for c in password):
            return False
        if self.require_number and not any(c.isdigit() for c in password):
            return False
        if self.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False
        return True
        
    def record_failed_attempt(self, user_identifier: str) -> bool:
        """Returns True if the user is now locked out."""
        current = self.failed_attempts.get(user_identifier, 0)
        self.failed_attempts[user_identifier] = current + 1
        return self.is_locked_out(user_identifier)
        
    def reset_failed_attempts(self, user_identifier: str):
        if user_identifier in self.failed_attempts:
            del self.failed_attempts[user_identifier]
            
    def is_locked_out(self, user_identifier: str) -> bool:
        return self.failed_attempts.get(user_identifier, 0) >= self.lockout_threshold

password_policy = PasswordPolicyManager()
