from fastapi import Body, APIRouter, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from typing import List
from datetime import datetime
import uvicorn
import databases

from base import DATABASE, app
from validation import (
    CreateUserValidator,
    UserValidator,
    LoginValidator,
)
from helpers import (
    encode_password,
    decode_password,
    genrate_token,
    verify_token,
)

from model import User

from serializer import user_serializer


database = databases.Database(DATABASE)
user_router = APIRouter()
auth_router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


@app.on_event('startup')
async def startup():
    await database.connect()

@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()



@user_router.get('/', response_model=List[UserValidator])
async def get_all_users(skip: int = 0, paginate: int = 20):
    users = User.select().offset(skip).limit(paginate)
    return await database.fetch_all(users)


@user_router.post('/', response_model=CreateUserValidator)
async def create_user(user: CreateUserValidator):
    query = User.select().where(User.c.username == user.username)
    is_exist = await database.fetch_one(query)
    if is_exist:
        response = {'detail':'Username exits', 'status': 406}
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)

    query = User.insert().values(
        username=user.username,
        password=encode_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        phone=user.phone,
        role=user.role,
    )
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}


@user_router.get('/{user_id}', response_model=UserValidator)
async def get_user(user_id: int):
    query = User.select().where(User.c.id == user_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'User not fount', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    return is_exist


@user_router.put('/{user_id}', response_model=CreateUserValidator)
async def update_user(user_id: int, user: UserValidator):
    query = User.select().where(User.c.id == user_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'User not fount', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    if user.username:
        query = User.select().where(User.c.username == user.username)
        is_exist_username = await database.fetch_one(query)
        if is_exist_username and is_exist_username.id != user_id:
            response = {'detail':'Username not available', 'status': 406}
            return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)

    query = User.update().where(User.c.id == user_id).values(
        username = user.username if user.username else is_exist.username,
        password = encode_password(user.password) if user.password else is_exist.password,
        first_name = user.first_name if user.first_name else is_exist.first_name,
        last_name = user.last_name if user.last_name else is_exist.last_name,
        phone = user.phone if user.phone else is_exist.phone,
        gender = user.gender if user.gender else is_exist.gender,
    )
    await database.execute(query)
    return {**user.dict(), "id": user_id}


@user_router.delete('/{user_id}')
async def delete_user(user_id: int):
    query = User.delete().where(User.c.id == user_id)
    await database.execute(query)
    response = {'detail':"User id: {} deleted successfully!".format(user_id), 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@auth_router.post('/login', response_model=LoginValidator)
async def login(user: LoginValidator):
    query = User.select().where(User.c.username == user.username)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':'Username not found', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    if is_exist.password != encode_password(user.password):
        response = {'detail':'Wrong password', 'status': 400}
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)

    data = {
        'user_id': is_exist.id,
        'role': is_exist.role
    }
    token = genrate_token(data)
    response = {'detail':'Login Success','auth token':  token, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@auth_router.post('/refresh')
async def refresh_token(token: str = Header(None)):
    user = verify_token(token)
    if not user:
        response = {'detail':'Invalid Token', 'status': 403}
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=response)

    token = genrate_token(user)
    response = {'detail':'Token Refreshed','auth token':  token, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)

app.include_router(user_router, prefix='/users')
app.include_router(auth_router, prefix='/auth')
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)