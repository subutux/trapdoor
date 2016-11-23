#from . import trapdoor

from trapdoor import config as conf
from trapdoor.core.exceptions import *

import trapdoor.cli.configuration
import trapdoor.cli.mib
import trapdoor.cli.db

import argparse
import logging
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
       trapdoor.cli.configuration.init_config(conf,args)
    
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
       trapdoor.cli.mib.add_mib(config,args)
        
    if args.init_database:
        trapdoor.cli.db.init_db(config)
    elif args.superuser:
        trapdoor.cli.db.create_superuser(config,args)
        
    if args.changepass:
        trapdoor.cli.db.change_password(config,args)
    if args.verifypass:
        trapdoor.cli.db.verify_password(config,args)
    return True