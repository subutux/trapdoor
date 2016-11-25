import trapdoor.core.mibs as mibs
import pkgutil
import importlib
import logging
log = logging.getLogger('trapdoor.core.handler')
log.addHandler(logging.NullHandler())
_HANDLERS = []
_HANDLERS_MODULES = {}
def load():
    _HANDLERS = []
    for item in pkgutil.iter_modules(__path__,'trapdoor.handlers.'):
        log.info("caching module {module}".format(module=item[1]))
        _HANDLERS.append(item[1])
        _HANDLERS_MODULES[item[1]] = importlib.import_module(item[1])
    return _HANDLERS


class Handler(object):
    """
    Base class for trap handlers
    """
    
    def __init__(self,config):
        self._config = config
        self._mibs = mibs.MibResolver()

    def trap(self,trap_oid,trap_args,trap_properties):
        log.error("module not handling trap")
        raise NotImplementedError()
