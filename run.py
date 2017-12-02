import asyncio
import signal
import json
import time

from aceserver import protocol

with open("config.json") as f:
    config = json.load(f)

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

loop = asyncio.get_event_loop()
# Bad idea?
loop.time = time.perf_counter
loop._clock_resolution = time.get_clock_info('perf_counter').resolution
loop.set_debug(True)

server = protocol.ServerProtocol(config, loop=loop)

try:
    # aioconsole debugging stuff :)
    loop.console.locals['server'] = loop.console.locals['protocol'] = server
except AttributeError:
    pass

try:
    loop.add_signal_handler(signal.SIGINT, server.stop)
    loop.add_signal_handler(signal.SIGTERM, server.stop)
except NotImplementedError:
    pass

try:
    loop.run_until_complete(server.run())
finally:
    server.stop()
    loop.close()
