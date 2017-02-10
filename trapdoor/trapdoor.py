from .core import trap as core_trap
from .core import web as core_web
from .core import queue as core_queue

import asyncio
# import functools
import signal
import sys
import logging
log = logging.getLogger('trapdoor')
log.addHandler(logging.NullHandler())
# asyncio.AbstractEventLoop.set_debug(enabled=True)
__version__ = "0.0.1b"


def main(config, web=True, trap=True):
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
        log.warning("got signal %s: exit" % signame)

        loop.create_task(Trapdoor_reciever.stop())
        loop.create_task(Web.stop())
        loop.call_later(0.5, loop.stop)
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                ask_exit)
    Q = core_queue.Queue
    if trap:
        Trapdoor_reciever = core_trap.trapReciever(config, Q, loop)
        asyncio.ensure_future(Trapdoor_reciever.register())
    if web:
        Web = core_web.Web(config, loop=loop)
        asyncio.ensure_future(Web.start())
    loop.run_forever()
    loop.close()
