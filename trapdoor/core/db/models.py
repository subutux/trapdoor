import sqlalchemy as sa
from sqlalchemy import Table, Column,  Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = sa.declarative_base()


class User(Base):
    __table_name__ = "user"
    id = Column(sa.Integer, primary_key=True)
    login = Column(sa.String(256),nullable=False)
    password = Column(sa.String(256),nullable=False)
    is_superuser = Column(sa.Boolean,nullable=False,
                          server_default='FALSE')
    disabled = Column(sa.Boolean,nullable=False,
                          server_default='FALSE')
    permissions = sa.relationship('permission.id')

class Permission(Base):
    __table_name__ = "permission"
    id = Column(sa.Integer, primary_key=True)
    user_id = Column(sa.Integer,sa.ForeignKey('user_login_key.id'))
    name = Column(sa.String(256),nullable=False)
    

class Host(Base):
    __table_name__ = 'host'
    id = Column(sa.Integer, primary_key=True)
    messages = sa.relationship('message')
    hostname = sa.Column(sa.String(256),nullable=False)
    ip = sa.Column(sa.String(256),nullable=False)
    active = sa.Column(sa.Boolean,nullable=False,server_default="FALSE")

class message(Base):
    __table_name__ = "message"
    id = Column(sa.Integer,primary_key=True)
    host_id = Column(sa.Integer,sa.ForeignKey('host.id'))
    oid = sa.Column('oid',sa.String(256), nullable=False)
    mib = sa.Column('mib',sa.String(256), nullable=False)
    variables = sa.relationship('variables')

class variable(Base):
    __table_name__ = 'variable'
    id = Column(sa.Integer,primary_key=True)
    var = Column(sa.String(256))
    val = Column(sa.String(256))
    message_id = Column(sa.Integer,sa.ForeignKey('message.id'))
