from trapdoor.core import mibs,exceptions
import logging
log = logging.getLogger('trapdoor.cli.mib')
log.addHandler(logging.NullHandler())

def add_mib(config,args):
    try:
        mibs.storeMib(config,args.add_mib,args.mibs,
        fetchRemote=args.allow_remote_mibs)
    except exceptions.MibCompileError:
        exit(1)
    except exceptions.MibCompileFailed:
        exit(1)
    finally:
        exit(0)
