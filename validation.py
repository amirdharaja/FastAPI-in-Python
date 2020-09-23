from pydantic import BaseModel, Field


class CreateUserValidator(BaseModel):
    username: str = Field(..., title='Username of the User', max_length=255)
    password: str = Field(..., title='Password of the User', min_length=6, max_length=255)
    first_name: str = Field(..., title='First name of the User', max_length=255)
    last_name: str = Field(None, title='Last name of the User', max_length=255)
    phone: str = Field(None, title='Phone number of the User', max_length=32)
    gender: str = Field(None, title='Gender of the User', max_length=32)
    role: str = Field(None, title='Role of the User', max_length=32)


class UserValidator(BaseModel):
    id: int = Field(None)
    username: str = Field(None, title='Username of the User', max_length=255)
    password: str = Field(None, title='Password of the User', min_length=6, max_length=255)
    first_name: str = Field(None, title='First name of the User', max_length=255)
    last_name: str = Field(None, title='Last name of the User', max_length=255)
    phone: str = Field(None, title='Phone number of the User', max_length=20)
    gender: str = Field(None, title='Gender of the User', max_length=32)
    role: str = Field(None, title='Role of the User', max_length=32)


class LoginValidator(BaseModel):
    username: str = Field(..., title='Username of the User', max_length=255)
    password: str = Field(..., title='Password of the User', min_length=6, max_length=255)