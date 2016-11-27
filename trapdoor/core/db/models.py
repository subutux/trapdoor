import sqlalchemy as sa
from sqlalchemy import Column, String, Integer
from sqlalchemy import ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import logging
log = logging.getLogger('trapdoor.core.db.models')
log.addHandler(logging.NullHandler())

Base = declarative_base()


class Permission(Base):
    __tablename__ = "permission"
    id = Column(Integer, primary_key=True, autoincrement=True)
    users = relationship("User", cascade="all, delete-orphan",
                         backref='permission')
    name = Column(String(256), nullable=False)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(256), nullable=False)
    password = Column(String(256), nullable=False)
    is_superuser = Column(Boolean, nullable=False,
                          server_default='0')
    disabled = Column(Boolean, nullable=False,
                      server_default='0')
    permissions = Column(Integer, ForeignKey(
        'permission.id'), primary_key=True, nullable=True)


class Variable(Base):
    __tablename__ = 'variable'
    id = Column(Integer, primary_key=True, autoincrement=True)
    var = Column(String(256))
    val = Column(String(256))
    message_id = Column(ForeignKey('message.id'))


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(ForeignKey('host.id'))
    timestamp = sa.Column(DateTime, default=sa.func.now())
    oid = sa.Column('oid', String(256), nullable=False)
    mib = sa.Column('mib', String(256), nullable=False)
    variables = relationship(Variable)


class Host(Base):
    __tablename__ = 'host'
    id = Column(Integer, primary_key=True, autoincrement=True)
    messages = relationship(Message)
    hostname = sa.Column(String(256), nullable=False)
    ip = sa.Column(String(256), nullable=False)
    created = sa.Column(DateTime, default=sa.func.now())
    active = sa.Column(Boolean, nullable=False, server_default="0")


class Filter(Base):
    __tablename__ = 'filter'
    id = Column(Integer, primary_key=True, autoincrement=True)
    oid = Column(String(256), nullable=True)
    host = Column(Integer, ForeignKey('host.id'),
                  primary_key=True, nullable=True)
    filter = Column(String(256), nullable=False)
    active = Column(Boolean, nullable=False, server_default='1')
