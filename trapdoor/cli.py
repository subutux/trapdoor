#from . import trapdoor
from .core import db
from .core import config as conf
from .core import authentication

import argparse
import logging
import getpass
import sys

LOGLEVELS = ["ERROR","WARNING","INFO","DEBUG"]

def main():
    parser = argparse.ArgumentParser(description="Store & filter traps",
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c','--config',
                        help="Config file",
                        default="/etc/trapdoor/trapdoor.yaml")

    starters = parser.add_mutually_exclusive_group()

    starters.add_argument('-T','--trap-only',
                       help="Only launch the snmp trap reciever",
                       action="store_true")
    starters.add_argument('-W','--web-only',
                           help="Only launch the Web manager",
                           action="store_true")
    starters.add_argument('--init-database',
                         help="Initialize the database",
                         action="store_true")
    starters.add_argument('--add-superuser',
                         help="Add a super user to the database",
                         dest="superuser", metavar="user")
    starters.add_argument('--change-password',
                         help="Change a users password",
                         dest="changepass", metavar="user")
    starters.add_argument('--verify-password',
                         help="Verify a users password",
                         dest="verifypass", metavar="user")

    parser.add_argument('-v','--verbose',
                         help="Increase verbosity",
                         action="count", default=0)


    args = parser.parse_args()
    
    # Setup logger
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)s:%(name)s] \
[%(levelname)-5.5s]  %(message)s")
    log = logging.getLogger("trapdoor")
    
    if args.verbose > len(LOGLEVELS):
        args.verbose = len(LOGLEVELS)
    log.setLevel(getattr(logging,LOGLEVELS[args.verbose]))

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)
    
    log.debug("Opening config file {}".format(args.config))
    try:
        config = conf.Config(args.config).get()
    except conf.ConfigNotFoundError as exc:
        log.error(exc)
        exit(1)
    except conf.ConfigNotParsedError as exc:
        log.error("Unable to parse configfile: {}".format(exc))
        exit(1)
    
        
    
    if hasattr(config,"log") and hasattr(config["log"],"file"):
        fileHandler = logging.FileHandler(str(config["log"]["file"]))
        fileHandler.setFormatter(logFormatter)
        log.addHandler(fileHandler)

    if args.init_database:
        
        log.debug("Config: {}".format(config))
        try:
            
            engine = db.engine.get_db_engine(user=config["db"]["user"],
                                             password=config["db"]["password"],
                                             db=config["db"]["database"],
                                             host=config["db"]["host"])
            
            db.engine.init_db(engine)
            
        except Exception as exc:
            log.error("Cannot initialize database: {}".format(exc))
    elif args.superuser:
        engine = db.engine.get_db_engine(user=config["db"]["user"],
                                         password=config["db"]["password"],
                                         db=config["db"]["database"],
                                         host=config["db"]["host"])
        
        session = db.engine.get_db_session(engine)
        
        
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
        
        
    if args.changepass:
        log.debug("Password update for user {}".format(args.changepass))
        engine = db.engine.get_db_engine(user=config["db"]["user"],
                                         password=config["db"]["password"],
                                         db=config["db"]["database"],
                                         host=config["db"]["host"])
        
        session = db.engine.get_db_session(engine)
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
    if args.verifypass:
        log.debug("Password update for user {}".format(args.verifypass))
        engine = db.engine.get_db_engine(user=config["db"]["user"],
                                         password=config["db"]["password"],
                                         db=config["db"]["database"],
                                         host=config["db"]["host"])
        
        session = db.engine.get_db_session(engine)
        user = authentication.get_user(session,args.verifypass)
        if user == None:
            log.error("Unknown user {}".format(args.verifypass))
            exit(1)
        # get user password
        pone = getpass.getpass(prompt="Password: ")
        authentication.verify_password(user,pone)
    return True