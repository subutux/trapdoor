import logging
from . import Handler
log = logging.getLogger('trapdoor.core.handler')
log.addHandler(logging.NullHandler())

__name__ = "log"
__description__ = "A simple handler for traps"

def setup(config):
    """
    Setup the handler & return the class instance
    """
    return logger(config)

class logger(Handler):
    def __init__(self,config):
        Handler.__init__(self,config)
    
    def trap(self,trap_oid,trap_args,trap_properties):
        args = ", ".join("=".join(_) for _ in trap_args.items())
        log.info(
            "TRAP:{oid} from {ip}: {args}".format(
                                           oid=trap_oid,
                                           ip=trap_properties["ipaddress"],
                                           args=args))
