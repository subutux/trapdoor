import asyncio
from aiohttp import web

import logging
log = logging.getLogger('trapdoor.core.web')
log_access = logging.getLogger('trapdoor.core.web.access')
log.addHandler(logging.NullHandler())

@asyncio.coroutine
def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


def Web(loop,port=8080):
	log.info("Launching web on port {}".format(port))

	app = web.Application(loop=loop)
	app.router.add_get('/', handle)
	app.router.add_get('/{name}', handle)
	handler = app.make_handler(logger=log, access_log=log_access)
	f = loop.create_server(handler, '0.0.0.0', port)
	srv = loop.run_until_complete(f)
	#web.run_app(app,port=port)
