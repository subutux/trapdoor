import asyncio
from . import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import aiomysql.sa
import logging
log = logging.getLogger('trapdoor.core.db.engine')
log.addHandler(logging.NullHandler())


def get_db_engine(host, user, password, db):
    url = "mysql+pymysql://{user}:{password}@{host}/{db}"

    log.debug("Creating connection to {}".format(
        url.format(
            user=user, password="*********", host=host, db=db)))
    url = url.format(
        user=user, password=password, host=host, db=db)
    engine = create_engine(url)
    return engine


def get_db_session(engine):
    log.debug("initialize new db session")
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(engine):
    log.debug("Creating tables")
    models.Base.metadata.create_all(engine)


class Engine(object):
    """
    The async DB Engine
    """

    def __init__(self, config):
        self._config = config
        self._engine = None
        self._session = None

    @asyncio.coroutine
    def connect(self):
        self._engine = yield from aiomysql.create_engine(
            user=self._config["db"]["user"],
            password=self._config["db"]["host"],
            host=self._config["db"]["host"],
            database=self._config["db"]["db"])

    def session(self):
        if self._session is None:
            self._session = sessionmaker(bind=self._engine)
        return self._session
