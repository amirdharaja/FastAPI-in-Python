from model import User

import hashlib, uuid
import jwt

JWT_SECRET = 'screel_labs_assessment_jwt_secret'
JWT_ALGORITHM = 'HS256'


def encode_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def decode_password(password):
    return hashlib.sha256(password.decode())

def genrate_token(data):
    token = jwt.encode(data, JWT_SECRET, JWT_ALGORITHM).decode('utf-8')
    return 'Token '+token

def verify_token(token):
    user_id = jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)
    return user_id
