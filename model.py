from sqlalchemy import (
    Table, Column, Integer, String, DateTime, ForeignKey, Enum, TIMESTAMP, MetaData, create_engine
)
from sqlalchemy.sql import func

from base import DATABASE

from datetime import datetime
import enum


metadata = MetaData()


class Gender(enum.Enum):
    male = 'm'
    female = 'f'
    other = 'o'


class Role(enum.Enum):
    user = 'u'
    admin = 'a'


User = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(255), unique=True, nullable=False),
    Column("password", String(1024), nullable=False),
    Column("first_name", String(255), nullable=False),
    Column("last_name", String(255), nullable=True),
    Column("phone", String(32), nullable=True),
    Column("gender", Enum(Gender), server_default='o'),
    Column("role", Enum(Role), server_default='u'),
)


engine = create_engine(
    DATABASE, connect_args={"check_same_thread": False}
)

metadata.create_all(engine)
