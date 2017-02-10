import sqlalchemy as sa
from sqlalchemy import MetaData, Table, Column, String
from sqlalchemy import Integer, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.dialects.mysql import TEXT
from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy.orm import relationship
import logging
log = logging.getLogger('trapdoor.core.db.models')
log.addHandler(logging.NullHandler())


Base = declarative_base()
metadata = MetaData()


Permission = Table('permission', metadata,
                   Column('id', Integer, primary_key=True, autoincrement=True),
                   Column('name', String(256), nullable=False)
                   )

User = Table('user', metadata,
              Column('id', Integer, primary_key=True, autoincrement=True),
              Column('login', String(256), nullable=False),
              Column('full_name', String(256), nullable=False),
              Column('password', String(256), nullable=False),
              Column('is_superuser', Boolean, nullable=False,
                     server_default='0'),
              Column('disabled', Boolean, nullable=False,
                     server_default='0'),
              Column('permissions', Integer, ForeignKey('permission.id'),
                     primary_key=True, nullable=True)
              )

Apikey = Table('apikey',metadata,
               Column('id',Integer, primary_key=True, autoincrement=True),
               Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
               Column('key', String(256), nullable=False),
               # Invalidate the key directly if there is not datetime given.
               Column('valid_until',DateTime,default=sa.func.now())
               )

Variable = Table('variable',metadata,
                 Column('id',Integer, primary_key=True,autoincrement=True),
                 Column('var',String(256)),
                 Column('val',String(256)),
                 Column('message_id',ForeignKey('message.id'),primary_key=True)
                 )

Message = Table('message',metadata,
                Column('id',primary_key=True,autoincrement=True),
                Column('host_id',ForeignKey('host.id'),primary_key=True),
                Column('timestamp',DateTime,default=sa.func.now()),
                Column('oid',String(256),nullable=False),
                Column('mib',String(256),nullable=False)
               )
Host = Table('host',metadata,
               Column('id',primary_key=True,autoincrement=True),
               Column('hostname',String(256)),
               Column('ip',String(256),nullable=False),
               Column('created',DateTime,default=sa.func.now()),
               Column('active',Boolean,nullable=False,server_default="0")
               )

Filter = Table('filter',metadata,
               Column('id',primary_key=True,autoincrement=True),
               Column('oid',String(256),nullable=False),
               Column('host_id',ForeignKey('host.id'),primary_key=True),
               Column('filter',String(256),nullable=False),
               Column('active',Boolean,nullable=False,server_default="0")
            )
