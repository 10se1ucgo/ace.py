import asyncio
import traceback
import typing

import enet

from aceserver import util


class BaseConnection:
    async def on_connect(self, data):
        pass

    async def on_disconnect(self):
        pass

    async def on_receive(self, packet: enet.Packet):
        pass



class BaseProtocol:
    def __init__(self, loop: asyncio.AbstractEventLoop, interface: str=None, port: int=32887, max_connections: int=32,
                 connection_factory=BaseConnection):
        self.loop: asyncio.AbstractEventLoop = loop
        self.host: enet.Host = enet.Host(enet.Address(interface, port), max_connections, 1, 0, 0)
        self.host.compress_with_range_coder()
        self.connection_factory = connection_factory

        self.connections: typing.Dict[enet.Peer, BaseConnection] = {}
        self.time = 0

    async def run(self):
        ip, port = util.get_ip(), self.host.address.port
        print(f"Running server on {ip}:{port}")
        print(f"Server identifier is {util.get_identifier(ip, port)}")

        # start = self.loop.time()
        last: float = self.loop.time()
        while self.loop.is_running():
            now = self.loop.time()
            dt = now - last
            self.time += dt
            await self.update(dt)
            await asyncio.sleep(1 / 64)
            # print(self.time, now - start, 1 / (dt or 1))
            last = now

    def stop(self):
        print("Shutting down...")
        for conn in self.connections:
            conn.disconnect()
        print("Disconnected clients")
        self.host.flush()
        print("Flushed host")

    async def update(self, dt):
        await self.net_update(dt)

    # def net_loop(self):
    #     while True:
    #         self.net()

    async def net_update(self, dt):
        try:
            if self.host is None:
                return
            event = await self.loop.run_in_executor(None, self.host.service, 0)
            event_type = event.type
            if not event or event_type == enet.EVENT_TYPE_NONE:
                return

            peer = event.peer
            future = None
            if event_type == enet.EVENT_TYPE_CONNECT:
                future = asyncio.ensure_future(self.on_connect(peer, event.data), loop=self.loop)
            elif event_type == enet.EVENT_TYPE_DISCONNECT:
                future = asyncio.ensure_future(self.on_disconnect(peer), loop=self.loop)
            elif event_type == enet.EVENT_TYPE_RECEIVE:
                future = asyncio.ensure_future(self.on_receive(peer, event.packet), loop=self.loop)
            if future:
                future.add_done_callback(net_finish)
        except:
            print("Ignoring exception in net_loop(): ")
            traceback.print_exc()

    async def on_connect(self, peer: enet.Peer, data: int):
        connection: typing.Optional[BaseConnection] = self.connections.get(peer)
        if connection is None:
            connection = self.connection_factory(self, peer)
            self.connections[peer] = connection

        await connection.on_connect(data)

    async def on_disconnect(self, peer: enet.Peer):
        print("disconnect BOY")
        connection: typing.Optional[BaseConnection] = self.connections.pop(peer, None)
        if not connection:
            return

        await connection.on_disconnect()

    async def on_receive(self, peer: enet.Peer, packet: enet.Packet):
        connection: typing.Optional[BaseConnection] = self.connections.get(peer)
        if not connection:
            return

        await connection.on_receive(packet)


def net_finish(future):
    e = future.exception()
    if e:
        raise e
