from trapdoor.core.db import engine as Engine
from trapdoor.core import authentication
import getpass
import logging
log = logging.getLogger('trapdoor.cli.db')
log.addHandler(logging.NullHandler())

def init_db(config):
    try:
        
        engine = Engine.get_db_engine(user=config["db"]["user"],
                                         password=config["db"]["password"],
                                         db=config["db"]["database"],
                                         host=config["db"]["host"])
        
        Engine.init_db(engine)
        
    except Exception as exc:
        log.error("Cannot initialize database: {}".format(exc))

def create_superuser(config,args):
    engine = Engine.get_db_engine(user=config["db"]["user"],
                                     password=config["db"]["password"],
                                     db=config["db"]["database"],
                                     host=config["db"]["host"])
    
    session = Engine.get_db_session(engine)
    
    
    # get user password
    pone = getpass.getpass(prompt="Password: ")
    ptwo = getpass.getpass(prompt="Password agian: ")
    
    if pone != ptwo:
        log.error("Passwords do not match!")
        exit(1)
    log.debug(session)
    group = authentication.permission_add(session,"Superuser")
    authentication.user_add(session,user=args.superuser,password=pone,
                            superuser=True,permission=group)

def change_password(config,args):
    log.debug("Password update for user {}".format(args.changepass))
    engine = Engine.get_db_engine(user=config["db"]["user"],
                                     password=config["db"]["password"],
                                     db=config["db"]["database"],
                                     host=config["db"]["host"])
    
    session = Engine.get_db_session(engine)
    user = authentication.get_user(session,args.changepass)
    if user == None:
        log.error("Unknown user {}".format(args.changepass))
        exit(1)
    # get user password
    pone = getpass.getpass(prompt="Password: ")
    ptwo = getpass.getpass(prompt="Password agian: ")
    
    if pone != ptwo:
        log.error("Passwords do not match!")
        exit(1)
    authentication.update_user_password(session,user,pone)

def verify_password(config,args):
    log.debug("Password update for user {}".format(args.verifypass))
    engine = Engine.get_db_engine(user=config["db"]["user"],
                                     password=config["db"]["password"],
                                     db=config["db"]["database"],
                                     host=config["db"]["host"])
    
    session = Engine.get_db_session(engine)
    user = authentication.get_user(session,args.verifypass)
    if user == None:
        log.error("Unknown user {}".format(args.verifypass))
        exit(1)
    # get user password
    pone = getpass.getpass(prompt="Password: ")
    authentication.verify_password(user,pone)