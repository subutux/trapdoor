#from . import trapdoor
from .core import db
from .core import config as conf
from .core import authentication
from .core import mibs
from .core.exceptions import *
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
    
    parser.add_argument('-v','--verbose',
                         help="Increase verbosity",
                         action="count", default=1)

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
    starters.add_argument('--init-config',
                         help="Create a config file containing the defaults",
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
    starters.add_argument('--add-mib',
                         help="Add a mib to trapdoor",
                         dest="add_mib", metavar="MIB")

    parser.add_argument('-m','--mibs',
                         help="Location to look for mibs when using --add-mib",
                         metavar="path", default=None)
    parser.add_argument('--allow-remote-mibs',
                         help="Fetch mibs from http://mibs.snmplabs.com/asn1/ \
when using --add-mib",
                         action="store_true", default=False)

    args = parser.parse_args()
    
    # Setup logger
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)s:%(name)s] \
[%(levelname)-5.5s]  %(message)s")
    log = logging.getLogger("trapdoor")
    
    if args.verbose > len(LOGLEVELS):
        args.verbose = len(LOGLEVELS)
    log.setLevel(getattr(logging,LOGLEVELS[args.verbose-1]))

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)
    
    # this needs to be here.
    
    if args.init_config:
        try:
            conf.writeDefaults(args.config)
        except Exception as e:
            log.error('Unable to write config! {}'.format(e))
            exit(1)
        exit(0)
    
    
    log.debug("Opening config file {}".format(args.config))
    try:
        config = conf.Config(args.config).get()
    except ConfigNotFoundError as exc:
        log.error(exc)
        exit(1)
    except ConfigNotParsedError as exc:
        log.error("Unable to parse configfile: {}".format(exc))
        exit(1)
    
        
    
    if hasattr(config,"log") and hasattr(config["log"],"file"):
        fileHandler = logging.FileHandler(str(config["log"]["file"]))
        fileHandler.setFormatter(logFormatter)
        log.addHandler(fileHandler)
    if args.mibs and not args.add_mib:
        log.error("-m, --mibs makes no sense without --add-mib!")
        exit(1)
    if args.add_mib:
        try:
            mibs.storeMib(config,args.add_mib,args.mibs,
            fetchRemote=args.allow_remote_mibs)
        except exceptions.MibCompileError:
            exit(1)
        except exceptions.MibCompileFailed:
            exit(1)
        finally:
            exit(0)
        
    if args.init_database:
        
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