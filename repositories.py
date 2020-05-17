from starlette.config import Config
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from starlette.authentication import BaseUser
from starlette_auth_toolkit.cryptography import (
    generate_random_string,
)

#
# Configuration from file:
#     DATABASE_URL=mysql://login:password@ip:port/table 
#
# Port: 
# - 3306 mysql.
# - 3307 mariadb.
#
config = Config('database.env')
DATABASE_URL = config('DATABASE_URL')

engine = create_engine(DATABASE_URL, echo=False) # req: sudo apt install libmariadbclient-dev
                                                 # python-mysqldb too?

# sqlalchemy
Base = declarative_base()

class Users(Base, BaseUser):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True)
    username = Column(String(180), nullable=False)
    username_canonical = Column(String(180), nullable=False, unique=True)
    email = Column(String(180), nullable=False)
    email_canonical = Column(String(180), nullable=False, unique=True)
    enabled = Column(TINYINT(1))
    password = Column(String(255))
    last_login = Column(Date)

    def __repr__(self):
        return "<Users(username='%s', email='%s', enabled='%d')>" % (
            self.username, self.email, self.enabled)

    #@property
    #def is_authenticated(self) -> bool:
    #    return True

class Tokens(Base):
    __tablename__ = "Tokens"

    token = Column(String(256), primary_key=True, default=generate_random_string(size=256))
    idUser = Column(Integer, ForeignKey('Users.id'))

    user = relationship("Users", back_populates="tokens")

    def __repr__(self):
        return "<Tokens(token='%s', idUser='%d')>" % (
            self.token, self.idUser)

class Friends(Base):
    __tablename__ = 'Friends'

    id = Column(Integer, primary_key=True)
    name = Column(String(80))
    genre = Column(VARCHAR(1))
    birthdate = Column(DateTime)
    idUser = Column(Integer, ForeignKey('Users.id'))

    user = relationship("Users", back_populates="friends")

    def __repr__(self):
        return "<Friends(name='%s', genre='%s', birthdate='%s')>" % (
            self.name, self.genre, self.birthdate)

Users.friends = relationship(
    "Friends", order_by=Friends.id, back_populates="user",
    cascade="all, delete, delete-orphan")

Users.tokens = relationship(
    "Tokens", order_by=Tokens.token, back_populates="user",
    cascade="all, delete, delete-orphan")

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

# Database table definitions.
metadata = sqlalchemy.MetaData()

#friends = sqlalchemy.Table(
#    "friends",
#    metadata,
#    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
#    sqlalchemy.Column("name", sqlalchemy.String),
#    #sqlalchemy.Column("completed", sqlalchemy.Boolean),
#)
