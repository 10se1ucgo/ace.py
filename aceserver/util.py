import asyncio
import ipaddress
import struct
from typing import Union, Tuple
from urllib import request, parse

__all__ = ["IDPool", "Event", "static_vars", "get_ip", "get_identifier", "read_identifier"]


class IDPool:
    def __init__(self, start: int=0, stop: int=32):
        self.ids = set(range(start, stop))

    def pop(self) -> int:
        id: int = self.ids.pop()
        return id

    def push(self, id: int):
        if id in self.ids:
            raise ValueError(f"id {id} has been freed already!")
        self.ids.add(id)
        print(self.ids)


class Event:
    def __init__(self):
        self._funcs = []

    def __iadd__(self, other):
        if not callable(other):
            raise TypeError("Event handler must be callable.")
        self._funcs.append(other)
        return self

    def __isub__(self, other):
        self._funcs.remove(other)
        return self

    def __call__(self, *args, **kwargs):
        for func in self._funcs:
            r = func(*args, **kwargs)
            if asyncio.iscoroutine(r):
                asyncio.ensure_future(r)


def static_vars(**kwargs):
    def wrapper(func):
        for var, obj in kwargs.items():
            setattr(func, var, obj)
        return func
    return wrapper


IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
def get_ip(getter: str="http://services.buildandshoot.com/getip") -> IPAddress:
    req = request.Request(url=getter, headers={'User-Agent': 'Mozilla/5.0'})
    resource = request.urlopen(req)
    return ipaddress.ip_address(resource.read().decode(resource.headers.get_content_charset()))


def get_identifier(address: Union[IPAddress, str, int, bytes], port: Union[str, int]=32887):
    address: IPAddress = ipaddress.ip_address(address)
    host = struct.unpack("<I", address.packed)[0]
    return f"aos://{host}:{port}"


def read_identifier(ident: str, default_port: int=32887) -> Tuple[IPAddress, int]:
    ident: parse.ParseResult = parse.urlparse(ident)
    if ident.scheme != "aos":
        raise ValueError("Not a valid identifier")
    pair = ident.netloc.split(":")
    if len(pair == 2):
        host, port = pair
    else:
        host, port = pair, default_port
    return ipaddress.ip_address(int(host)), int(port)
