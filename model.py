from sqlalchemy import (
    Table, Column, Integer, Float, Boolean, String, DateTime, Text,
    ForeignKey, Enum, TIMESTAMP, MetaData, create_engine
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from base import DATABASE
from datetime import datetime
import enum


metadata = MetaData()


class Gender(enum.Enum):
    m = 'male'
    f = 'female'
    o = 'other'


class Role(enum.Enum):
    u = 'user'
    r = 'recruiter'
    a = 'admin'

class JobType(enum.Enum):
    ft = 'full time'
    pt = 'part time'
    i = 'internship'

class SkillType(enum.Enum):
    p = 'primary'
    s = 'secondary'

class SkillLevel(enum.Enum):
    beginner = 'beginner'
    intermediate = 'intermediate'
    advanced = 'advanced'

class JobStatus(enum.Enum):
    cr = 'created'
    a = 'applied'
    s = 'selected'
    r = 'rejected'
    f = 'filled'
    cl = 'closed'
    d = 'deleted'


User = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(255), unique=True, nullable=False),
    Column("password", String(1024), nullable=False),
    Column("first_name", String(255), nullable=False),
    Column("last_name", String(255), nullable=True),
    Column("phone", String(32), nullable=True),
    Column("gender", Enum(Gender), default='o'),
    Column("role", Enum(Role), default='u'),
)

JobCategory = Table(
    "job_categories",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("added_by", Integer, ForeignKey('users.id')),
    Column("name", String(255), nullable=False, unique=True),
)

Job = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("category", String, ForeignKey('job_categories.name'), nullable=False),
    Column("created_by", Integer, ForeignKey('users.id')),
    Column("company_name", String(255), nullable=True),
    Column("job_title", String(255), nullable=True),
    Column("job_type", Enum(JobType), default='f'),
    Column("experiance_min", Float, nullable=True),
    Column("experiance_max", Float, nullable=True),
    Column("job_count", Integer, nullable=True),
    Column("location", String(1024), nullable=True),
    Column("status", Enum(JobStatus), default='cr'),
    Column("description_short", String(255), nullable=True),
    Column("description_long", Text, nullable=True),
)

Skill = Table(
    "skills",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), unique=True, nullable=True),
    Column("type", Enum(SkillType), nullable=True),
    Column("level", Enum(SkillLevel), nullable=True),
    Column("job_id", Integer, ForeignKey('jobs.id'), unique=False),
)

AppliedJob = Table(
    "applied_jobs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey('users.id'), unique=False),
    Column("job_id", Integer, ForeignKey('jobs.id'), unique=False),
    Column("status", Enum(JobStatus), default='cr'),
)

FavouriteJob = Table(
    "favourite_jobs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey('users.id'), unique=False),
    Column("job_id", Integer, ForeignKey('jobs.id'), unique=False),
    Column("is_liked", Boolean),
)



engine = create_engine(DATABASE, connect_args={"check_same_thread": False})

metadata.create_all(engine)