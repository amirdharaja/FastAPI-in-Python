from fastapi import Body, APIRouter, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from typing import List
from datetime import datetime
import uvicorn
import databases
from pluck import pluck

from base import DATABASE, app
from validation import (
    UserValidator,
    LoginValidator,
    JobCategoryValidator,
    JobValidator,
    AppliedJobValidator,
    FavouriteJobValidator
)
from helpers import (
    encode_password,
    decode_password,
    genrate_token,
    verify_token,
    verify_token_with_role,
)

from model import engine, User, JobCategory, Job, FavouriteJob, AppliedJob, Skill

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind = engine)
session = Session()


database = databases.Database(DATABASE)
user_router = APIRouter()
auth_router = APIRouter()
job_router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8080'],
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


@user_router.post('/', response_model=UserValidator)
async def create_user(user: UserValidator):
    query = User.select().where(User.c.username == user.username)
    is_exist = await database.fetch_one(query)
    if is_exist:
        response = {'detail':'USERNAME NOT AVAILABLE', 'status': 406}
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
    return {**user.dict(), "ID": last_record_id}


@user_router.get('/{user_id}', response_model=UserValidator)
async def get_user(user_id: int):
    query = User.select().where(User.c.id == user_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'USER NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    return is_exist


@user_router.put('/{user_id}', response_model=UserValidator)
async def update_user(user_id: int, user: UserValidator, token: str = Header(None)):
    query = User.select().where(User.c.id == user_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'USER NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    if user_id != authenticated_user['user_id']:
        response = {'detail':'UNAUTHORIZED ACCESS(YOU CAN UPDATE YOUR ACCOUNT ONLY)', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    if user.username:
        query = User.select().where(User.c.username == user.username)
        is_exist_username = await database.fetch_one(query)
        if is_exist_username and is_exist_username.id != user_id:
            response = {'detail':'USERNAME NOT AVAILABLE', 'status': 406}
            return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)

    query = User.update().where(User.c.id == user_id).values(
        username = user.username if user.username else is_exist.username,
        password = encode_password(user.password) if user.password else is_exist.password,
        first_name = user.first_name if user.first_name else is_exist.first_name,
        last_name = user.last_name if user.last_name else is_exist.last_name,
        phone = user.phone if user.phone else is_exist.phone,
        gender = user.gender if user.gender else is_exist.gender,
        role = user.role if user.role else is_exist.role,
    )
    await database.execute(query)
    return {**user.dict(), "ID": user_id}


@user_router.delete('/{user_id}')
async def delete_user(user_id: int, token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    if user_id != authenticated_user['user_id']:
        response = {'detail':'UNAUTHORIZED ACCESS(YOU CAN DELETE YOUR ACCOUNT ONLY)', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = User.delete().where(User.c.id == user_id)
    await database.execute(query)
    response = {'detail':"USER ID: {} DELETED SUCCESSFULLY".format(user_id), 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@auth_router.post('/login', response_model=LoginValidator)
async def login(user: LoginValidator):
    query = User.select().where(User.c.username == user.username)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':'USERNAME NOT AVAILABLE', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    if is_exist.password != encode_password(user.password):
        response = {'detail':'WRONG PASSWORD', 'status': 400}
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)

    data = {
        'user_id': is_exist.id,
        'role': is_exist.role.value
    }
    token = genrate_token(data)
    response = {'detail':'LOGIN SUCCESS','token':  token, 'name': is_exist.first_name, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@auth_router.post('/refresh')
async def refresh_token(token: str = Header(None)):
    user = verify_token(token)
    if not user:
        response = {'detail':'INVALID OR EXPIRED TOKEN', 'status': 403}
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=response)

    token = genrate_token(user)
    response = {'detail':'TOKEN REFRESHED','token':  token, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@job_router.post('/', response_model=JobValidator)
async def create_job(job: JobValidator, token: str = Header(None)):
    authenticated_user = verify_token_with_role(token, expected_role='recruiter')
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = Job.insert().values(
        created_by=authenticated_user['user_id'],
        category=job.category,
        company_name=job.company_name,
        job_title=job.job_title,
        job_type=job.job_type,
        experiance_min=job.experiance_min,
        experiance_max=job.experiance_max,
        job_count=job.job_count,
        location=job.location,
        status='cr',
        description_short=job.description_short,
        description_long=job.description_long,
    )
    session.execute(query)
    session.commit()
    return {**job.dict()}


@job_router.post('/category', response_model=JobCategoryValidator)
async def create_category(category: JobCategoryValidator, token: str = Header(None)):
    authenticated_user = verify_token_with_role(token, expected_role='recruiter')
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = JobCategory.insert().values(
        added_by=authenticated_user['user_id'],
        name=category.name,
    )
    session.execute(query)
    session.commit()
    return {**category.dict()}


@job_router.get('/category', response_model=List[JobCategoryValidator])
async def get_categories(skip: int = 0):
    categories = JobCategory.select().offset(skip)
    return await database.fetch_all(categories)


@job_router.get('/{job_id}', response_model=JobValidator)
async def get_job(job_id: int):
    query = Job.select().where(Job.c.id == job_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'JOB NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    return is_exist


@job_router.put('/{job_id}', response_model=JobValidator)
async def update_job(job_id: int, job: JobValidator, token: str = Header(None)):
    query = Job.select().where(Job.c.id == job_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'JOB NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    authenticated_user = verify_token_with_role(token, expected_role='recruiter')
    if not authenticated_user or is_exist.created_by != authenticated_user['user_id']:
        response = {'detail':'UNAUTHORIZED ACCESS(ONLY JOB OWNER CAN UPDATE THE JOB)', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = Job.update().where(Job.c.id == job_id).values(
        company_name = job.company_name if job.company_name else is_exist.company_name,
        job_title = job.job_title if job.job_title else is_exist.job_title,
        job_type = job.job_type if job.job_type else is_exist.job_type,
        experiance_min = job.experiance_min if job.experiance_min else is_exist.experiance_min,
        experiance_max = job.experiance_max if job.experiance_max else is_exist.experiance_max,
        job_count = job.job_count if job.job_count else is_exist.job_count,
        location = job.location if job.location else is_exist.location,
        status = job.status if job.status else is_exist.status,
        description_short = job.description_short if job.description_short else is_exist.description_short,
        description_long = job.description_long if job.description_long else is_exist.description_long,
    )
    last_record_id = await database.execute(query)
    await database.execute(query)
    return {**job.dict(), "ID": last_record_id}


@job_router.delete('/{job_id}')
async def delete_job(job_id: int, token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = Job.select().where(Job.c.id == job_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'JOB NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    if is_exist.created_by != authenticated_user['user_id']:
        response = {'detail':'UNAUTHORIZED ACCESS(YOU CAN DELETE YOUR JOB ONLY)', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = Job.update().where(Job.c.id == job_id).values(
        status = 'd'
    )
    await database.execute(query)
    response = {'detail':"JOB ID: {} DELETED SUCCESSFULLY".format(job_id), 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@job_router.get('/', response_model=List[JobValidator])
async def get_all_jobs(skip: int = 0, paginate: int = 20):
    jobs = Job.select().offset(skip).limit(paginate)
    return await database.fetch_all(jobs)


@job_router.get('/my/posted', response_model=List[JobValidator])
async def get_all_my_posted_jobs(token: str = Header(None)):
    authenticated_user = verify_token_with_role(token, expected_role='recruiter')
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    jobs = session.query(Job).filter(Job.c.created_by == authenticated_user['user_id'])
    all_jobs = []
    for job in jobs:
        if job and job.status.value == 'deleted':
            pass
        else:
            all_jobs.append({
                'id': job.id,
                'company_name': job.company_name,
                'job_title': job.job_title,
                'job_type': job.job_type.value,
                'experiance_min': job.experiance_min,
                'experiance_max': job.experiance_max,
                'job_count': job.job_count,
                'location': job.location,
                'job_status': job.status.value if job.status else 'NA',
            })
    response = {'Jobs': all_jobs, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@user_router.post('/jobs/{job_id}', response_model=AppliedJobValidator)
async def apply_job(job_id: int, job: AppliedJobValidator, token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = Job.select().where(Job.c.id == job_id)
    is_exist = await database.fetch_one(query)
    if not is_exist:
        response = {'detail':  'REQUESTED JOB NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    query = session.query(AppliedJob).filter(AppliedJob.c.job_id == job_id, AppliedJob.c.user_id == authenticated_user['user_id']).first()
    if query:
        response = {'detail':  'ALREADY APPLIED', 'status': 406}
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=response)

    query = AppliedJob.insert().values(
        user_id=authenticated_user['user_id'],
        job_id=job_id,
        status='applied',
    )
    apply = AppliedJob.insert().values(user_id=authenticated_user['user_id'], job_id=job_id, status='a')
    session.execute(apply)
    session.commit()
    response = {'detail':  'SUCCESSFULLY APPLIED', 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@user_router.get('/jobs/my/{apply_id}')
async def get_my_job(apply_id: int, token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    my_job = session.query(AppliedJob).filter(AppliedJob.c.id == apply_id).first()
    if not my_job:
        response = {'detail':  'JOB NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    job = session.query(Job).filter(Job.c.id == my_job.job_id).first()
    if not job:
        response = {'detail':  'JOB NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    recruiter = session.query(User).filter(User.c.id == job.created_by).first()
    recruiter_details = 'NA'
    if recruiter:
        recruiter_details = {
            'id': recruiter.id,
            'first_name': recruiter.first_name,
            'last_name': recruiter.last_name,
            'email': recruiter.username,
            'phone': recruiter.phone,
            'gender': recruiter.gender,
        }
    data = {
        'my_status': my_job.status.value if my_job.status else 'NA',
        'job_details': {
            'id': job.id,
            'company_name': job.company_name,
            'job_title': job.job_title,
            'job_type': job.job_type,
            'experiance_min': job.experiance_min,
            'experiance_max': job.experiance_max,
            'job_count': job.job_count,
            'location': job.location,
            'job_status': job.status.value if job.status else 'NA',
        },
        'recruiter_details': recruiter_details
    }

    response = {'Job details': data, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@user_router.get('/jobs/my')
async def get_my_all_jobs(token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    my_jobs = session.query(AppliedJob).filter(AppliedJob.c.user_id == authenticated_user['user_id'])
    if my_jobs.count() == 0:
        response = {'detail':  'JOBS NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    job_ids = pluck(my_jobs, 'job_id')
    job_ids = set(job_ids)
    total_jobs = len(job_ids)
    jobs = session.query(Job).filter(Job.c.id.in_(job_ids))
    if jobs.count() == 0:
        response = {'detail':  'JOBS NOT FOUND', 'status': 404}
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)

    my_all_jobs = []
    for my_job in my_jobs:
        for job in jobs:
            if my_job.job_id == job.id:
                data = {
                    'my_status': my_job.status.value if my_job.status else 'NA',
                    'job_details': {
                        'id': job.id,
                        'company_name': job.company_name,
                        'job_title': job.job_title,
                        'job_type': job.job_type.value,
                        'experiance_min': job.experiance_min,
                        'experiance_max': job.experiance_max,
                        'job_count': job.job_count,
                        'location': job.location,
                        'job_status': job.status.value if job.status else 'NA',
                    }
                }
                my_all_jobs.append(data)

    response = {'Total': total_jobs, 'Jobs': my_all_jobs, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@user_router.post('/favourite/{job_id}')
async def add_favourite(job_id: int, token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = session.query(FavouriteJob).filter(FavouriteJob.c.user_id==authenticated_user['user_id'], FavouriteJob.c.job_id==job_id).first()
    if not query:
        query = FavouriteJob.insert().values(
            user_id=authenticated_user['user_id'],
            job_id=job_id,
            is_liked=True,
        )
        session.execute(query)
        session.commit()

    response = {'detail':'FAVOURITE JOB ADDED', 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@user_router.delete('/favourite/{favourite_id}')
async def remove_favourite(favourite_id: int, token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    query = FavouriteJob.delete().where(FavouriteJob.c.id == favourite_id)
    await database.execute(query)
    response = {'detail':"FAVOURITE JOB REMOVED", 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@user_router.get('/favourites/all')
async def get_favourite(token: str = Header(None)):
    authenticated_user = verify_token(token)
    if not authenticated_user:
        response = {'detail':'UNAUTHORIZED ACCESS', 'status': 401}
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response)

    favourites = session.query(FavouriteJob).all()
    all_favourite = []
    for d in favourites:
        data = {
            'id': d.id,
            'user_id': d.user_id,
            'job_id': d.job_id,
        }
        all_favourite.append(data)
    response = {'Favourites':all_favourite, 'status': 200}
    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


app.include_router(user_router, prefix='/users')
app.include_router(auth_router, prefix='/auth')
app.include_router(job_router, prefix='/jobs')
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)