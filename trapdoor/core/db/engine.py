import asyncio
from . import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import aiomysql.sa
import logging
log = logging.getLogger('trapdoor.core.db.engine')
log.addHandler(logging.NullHandler())


def get_db_engine(host, user, password, db):
    url = "mysql+pymysql://{user}:{password}@{host}/{db}?charset=utf8mb4&use_unicode=1"

    log.debug("Creating connection to {}".format(
        url.format(
            user=user, password="*********", host=host, db=db)))
    url = url.format(
        user=user, password=password, host=host, db=db)
    engine = create_engine(url,encoding="utf-8")
    return engine


def get_db_session(engine):
    log.debug("initialize new db session")
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(engine):
    log.debug("Creating tables")
    tables = models.metadata.tables.keys()
    models.metadata.create_all(engine)


class Engine(object):
    """
    The async DB Engine
    """

    def __init__(self, config):
        self._config = config
        self.engine = None

    @asyncio.coroutine
    def connect(self):
        self.engine = yield from aiomysql.sa.create_engine(
            user=self._config["db"]["user"],
            password=self._config["db"]["password"],
            host=self._config["db"]["host"],
            db=self._config["db"]["database"],
            autocommit=True, charset='utf8mb4',
            use_unicode=True)
    
    @asyncio.coroutine
    def disconnect(self):
        
        log.debug("Closing connections")
        self.engine.close()
        
        log.debug("Terminating connections")
        self.engine.terminate()
        log.debug("Waiting for close")
        yield from self.engine.wait_closed()
        log.debug("close")
        
        
