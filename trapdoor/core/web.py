import asyncio
from aiohttp import web
from trapdoor.core.db import Engine

import logging
log = logging.getLogger('trapdoor.core.web')
log_access = logging.getLogger('trapdoor.core.web.access')
log.addHandler(logging.NullHandler())


class Web(object):
    def __init__(self, config, loop=None):
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        self._config = config
        self.app = None
        self.handler = None

    @asyncio.coroutine
    def handle(self, request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    @asyncio.coroutine
    def start(self):
        port = self._config["web"]["transport"]["ipv4"]["port"]
        listen = self._config["web"]["transport"]["ipv4"]["listen"]

        log.info("Launching web on {}:{}".format(listen, port))

        self.app = web.Application(loop=self.loop)
        self.app.db = Engine(self._config)
        yield from self.app.db.connect()
        self.app.router.add_get('/', self.handle)
        self.app.router.add_get('/{name}', self.handle)
        self.handler = self.app.make_handler(logger=log, access_log=log_access)
        self._server = self.loop.create_server(self.handler, listen, port)
        # srv = loop.run_until_complete(f)
        yield from self._server
        # web.run_app(app,port=port)

    @asyncio.coroutine
    def stop(self):
        log.warning("Stopping Web")
        yield from self.app.shutdown()
        yield from self.app.cleanup()
