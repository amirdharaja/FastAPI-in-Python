from model import User

import hashlib, uuid
import jwt
from datetime import datetime, timedelta

JWT_SECRET = 'screel_labs_assessment_jwt_secret'
JWT_ALGORITHM = 'HS256'


def encode_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def decode_password(password):
    return hashlib.sha256(password.decode())

def genrate_token(user):
    data={
        'user_id':user['user_id'],
        'role':user['role'],
        'expire':str(datetime.now() + timedelta(days=30)),
    }
    token = jwt.encode(data, JWT_SECRET, JWT_ALGORITHM).decode('utf-8')
    return 'Token '+token

def verify_token(token):
    try:
        user = jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)
        return user
    except:
        return False
