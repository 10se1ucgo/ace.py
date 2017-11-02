import asyncio
import sys

from aceserver import protocol

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


loop = asyncio.get_event_loop()
server = protocol.ServerProtocol(loop)
loop.run_until_complete(server.run())
loop.close()
