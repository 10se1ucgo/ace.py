import asyncio
import traceback
import typing

import enet

from aceserver import util


class BaseConnection:
    def on_connect(self, data):
        pass

    def on_disconnect(self):
        pass

    def on_receive(self, packet: enet.Packet):
        pass


class BaseProtocol:
    def __init__(self, loop: asyncio.AbstractEventLoop, interface: str="", port: int=32887, max_connections: int=32,
                 connection_factory=BaseConnection):
        self.loop: asyncio.AbstractEventLoop = loop
        self.host: enet.Host = enet.Host(enet.Address(interface, port), max_connections, 1, 0, 0)
        self.host.compress_with_range_coder()
        self.host.intercept = self.intercept
        self.connection_factory = connection_factory

        self.connections: typing.Dict[enet.Peer, BaseConnection] = {}

        self.time = 0
        self.running = True

    async def run(self):
        ip, port = util.get_ip(), self.host.address.port
        print(f"Running server on {ip}:{port}")
        print(f"Server identifier is {util.get_identifier(ip, port)}")

        last: float = self.loop.time()
        while self.running:
            now = self.loop.time()
            dt = now - last
            self.time += dt
            try:
                self.update(dt)
            except Exception:
                print("Ignoring exception in update(): ")
                traceback.print_exc()
            await asyncio.sleep(1 / 30)
            # print(self.time, dt, 1 / dt)
            last = now

    def stop(self):
        self.running = False
        print("Shutting down...")
        for peer in self.connections.keys():
            peer.disconnect()
        print("Disconnected clients")
        self.host.flush()
        print("Flushed host")

    def update(self, dt):
        self.net_update()

    def net_update(self):
        while True:
            try:
                if self.host is None:
                    return
                event = self.host.service(0)
                event_type = event.type
                if not event or event_type == enet.EVENT_TYPE_NONE:
                    return

                peer = event.peer
                if event_type == enet.EVENT_TYPE_CONNECT:
                    self.on_connect(peer, event.data)
                elif event_type == enet.EVENT_TYPE_DISCONNECT:
                    self.on_disconnect(peer)
                elif event_type == enet.EVENT_TYPE_RECEIVE:
                    self.on_receive(peer, event.packet)
            except:
                print("Ignoring exception in net_loop(): ")
                traceback.print_exc()

    def connect(self, connection_factory: typing.Type[BaseConnection], addr: enet.Address, channels: int, data: int):
        peer = self.host.connect(addr, channels, data)
        connection = connection_factory(self, peer)
        self.connections[peer] = connection
        return connection

    def on_connect(self, peer: enet.Peer, data: int):
        connection: typing.Optional[BaseConnection] = self.connections.get(peer)
        if connection is None:
            connection = self.connection_factory(self, peer)
            self.connections[peer] = connection

        connection.on_connect(data)

    def on_disconnect(self, peer: enet.Peer):
        connection: typing.Optional[BaseConnection] = self.connections.pop(peer, None)
        if not connection:
            return

        connection.on_disconnect()

    def on_receive(self, peer: enet.Peer, packet: enet.Packet):
        connection: typing.Optional[BaseConnection] = self.connections.get(peer)
        if not connection:
            return

        connection.on_receive(packet)

    def intercept(self, address: enet.Address, data: bytes):
        pass


def net_finish(future):
    e = future.exception()
    if e:
        raise e
