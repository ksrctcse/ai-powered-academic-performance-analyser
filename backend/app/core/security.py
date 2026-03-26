
from jose import jwt
from werkzeug.security import generate_password_hash, check_password_hash

SECRET_KEY = "SECRET"

def hash_password(password: str) -> str:
    """
    Hash password using werkzeug's pbkdf2 method.
    This is simple, secure, and doesn't have the 72-byte limit of bcrypt.
    """
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed version"""
    return check_password_hash(hashed_password, plain_password)

def create_token(data: dict) -> str:
    """Create JWT token"""
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

