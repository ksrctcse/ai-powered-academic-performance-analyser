
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = "SECRET"
pwd = CryptContext(schemes=["bcrypt"])

def hash_password(p): return pwd.hash(p)
def verify(p, h): return pwd.verify(p, h)
def create_token(data): return jwt.encode(data, SECRET_KEY, algorithm="HS256")
