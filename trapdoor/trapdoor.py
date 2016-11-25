import asyncio
import functools
import signal, sys
import logging
log = logging.getLogger('trapdoor')
log.addHandler(logging.NullHandler())
from .core import trap as core_trap
from .core import web as core_web
from .core import queue as core_queue
#asyncio.AbstractEventLoop.set_debug(enabled=True)

    

def main(config,web=True,trap=True):
    logasync = logging.getLogger("asyncio")
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)s:%(name)s] \
[%(levelname)-5.5s]  %(message)s")

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logasync.addHandler(consoleHandler)
    
    loop = asyncio.get_event_loop()
   
    def ask_exit(signame="QUIT"):
        """
        http://stackoverflow.com/q/23313720
        """
        log.error("got signal %s: exit" % signame)
        loop.stop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                ask_exit)
    Q = core_queue.Queue
    if trap:
        Trapdoor_reciever = core_trap.trapReciever(config,Q,loop)
        loop.create_task(Trapdoor_reciever.register())
    if web:
        log.info("Web not implemented yet.")
    loop.run_forever()
    

