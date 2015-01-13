#!/usr/bin/env python3
"""Example for aiohttp.web websocket server
"""

import asyncio
import os
from aiohttp.web import (Application, Response,
                         WebSocketResponse, WebSocketDisconnectedError)

WS_FILE = os.path.join(os.path.dirname(__file__), 'websocket.html')


@asyncio.coroutine
def wshandler(request):
    resp = WebSocketResponse()
    ok, protocol = resp.can_start(request)
    if not ok:
        with open(WS_FILE, 'rb') as fp:
            return Response(body=fp.read(), content_type='text/html')

    resp.start(request)
    print('Someone joined.')
    for ws in request.app['sockets']:
        ws.send_str('Someone joined')
    request.app['sockets'].append(resp)

    try:
        while True:
            msg = yield from resp.receive_str()
            print(msg)
            for ws in request.app['sockets']:
                if ws is not resp:
                    ws.send_str(msg)
    except WebSocketDisconnectedError:
        request.app['sockets'].remove(resp)
        print('Someone disconnected.')
        for ws in request.app['sockets']:
            ws.send_str('Someone disconnected.')
        raise


@asyncio.coroutine
def init(loop):
    app = Application(loop=loop)
    app['sockets'] = []
    app.router.add_route('GET', '/', wshandler)

    handler = app.make_handler()
    srv = yield from loop.create_server(handler, '127.0.0.1', 8080)
    print("Server started at http://127.0.0.1:8080")
    return srv, handler

loop = asyncio.get_event_loop()
srv, handler = loop.run_until_complete(init(loop))
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(handler.finish_connections())