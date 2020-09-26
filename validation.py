from pydantic import BaseModel, Field
from datetime import date

from model import Role, Gender, JobType, JobStatus


class UserValidator(BaseModel):
    id: int = Field(None)
    username: str = Field(..., title='Username of the User', max_length=255)
    password: str = Field(..., title='Password of the User', min_length=6, max_length=255)
    first_name: str = Field(..., title='First name of the User', max_length=255)
    last_name: str = Field(None, title='Last name of the User', max_length=255)
    phone: str = Field(None, title='Phone number of the User', max_length=32)
    gender: Gender = Field(None, title='Gender of the User')
    role: Role = Field(None)

class LoginValidator(BaseModel):
    username: str = Field(..., title='Username of the User', max_length=255)
    password: str = Field(..., title='Password of the User', min_length=6, max_length=255)

class JobCategoryValidator(BaseModel):
    id: int = Field(None)
    added_by: int = Field(None)
    name: str = Field(..., title='Job category name', max_length=255)

class JobValidator(BaseModel):
    id: int = Field(None)
    created_by: int = Field(None)
    category: str = Field(..., title='Job category')
    company_name: str = Field(..., title='Company Name', max_length=255)
    job_title: str = Field(..., title='Job Title', max_length=255)
    job_type: JobType = Field(..., title='Type of the Job')
    experiance_min: float = Field(..., title='Minimum experiance required for the Job')
    experiance_max: float = Field(..., title='Maximum experiance required for the Job')
    job_count: int = Field(..., title='Available Job count')
    location: str = Field(..., title='Job (Company) Location', max_length=1024)
    status: JobStatus = Field(None, title='Job status')
    description_short: str = Field(..., title='Short description about job', max_length=255)
    description_long: str = Field(None, title='Long description about job')

class FavouriteJobValidator(BaseModel):
    user_id: int = Field(..., title='User ID')
    job_id: int = Field(..., title='Job ID')

class AppliedJobValidator(BaseModel):
    job_id: int = Field(None, title='Company Name')
    status: JobStatus = Field(None, title='Status of the Job')