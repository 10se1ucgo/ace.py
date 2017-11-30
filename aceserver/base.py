import asyncio
import traceback
import typing
import time as t

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
    def __init__(self, loop: asyncio.AbstractEventLoop, interface: str="", port: int=32887, max_connections: int=32,
                 connection_factory=BaseConnection):
        self.loop: asyncio.AbstractEventLoop = loop
        self.host: enet.Host = enet.Host(enet.Address(interface, port), max_connections, 1, 0, 0)
        self.host.compress_with_range_coder()
        self.host.intercept = self.intercept
        self.connection_factory = connection_factory

        self.connections: typing.Dict[enet.Peer, connection_factory] = {}

        self.time = 0
        self.running = True

    async def run(self):
        ip, port = util.get_ip(), self.host.address.port
        print(f"Running server on {ip}:{port}")
        print(f"Server identifier is {util.get_identifier(ip, port)}")

        # start = self.loop.time()
        last: float = t.perf_counter()
        while self.running:
            now = t.perf_counter()
            dt = now - last
            self.time += dt
            try:
                self.update(dt)
            except Exception:
                print("Ignoring exception in update(): ")
                traceback.print_exc()
            await asyncio.sleep(1 / 50)
            # print(self.time, 1 / (dt or 1))
            last = now

    def stop(self):
        self.running = False
        print("Shutting down...")
        for conn in self.connections:
            conn.disconnect()
        print("Disconnected clients")
        self.host.flush()
        print("Flushed host")

    def update(self, dt):
        self.net_update()

    def net_update(self):
        while True:
            try:
                if self.host is None:
                    break
                event = self.host.service(0)
                event_type = event.type
                if not event or event_type == enet.EVENT_TYPE_NONE:
                    break

                peer = event.peer
                task = None
                if event_type == enet.EVENT_TYPE_CONNECT:
                    task = self.loop.create_task(self.on_connect(peer, event.data))
                elif event_type == enet.EVENT_TYPE_DISCONNECT:
                    task = self.loop.create_task(self.on_disconnect(peer))
                elif event_type == enet.EVENT_TYPE_RECEIVE:
                    task = self.loop.create_task(self.on_receive(peer, event.packet))
                if task:
                    task.add_done_callback(net_finish)
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
        connection: typing.Optional[BaseConnection] = self.connections.pop(peer, None)
        if not connection:
            return

        await connection.on_disconnect()

    async def on_receive(self, peer: enet.Peer, packet: enet.Packet):
        connection: typing.Optional[BaseConnection] = self.connections.get(peer)
        if not connection:
            return

        await connection.on_receive(packet)

    def intercept(self, address: enet.Address, data: bytes):
        pass


def net_finish(future):
    e = future.exception()
    if e:
        raise e
