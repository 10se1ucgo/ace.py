import math
import inspect
import traceback
import ipaddress
import struct
import weakref
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


class Event:
    def __init__(self, overridable=False):
        self._funcs = []
        self.overridable = overridable

    def __iadd__(self, other):
        if not callable(other):
            raise TypeError("Event handler must be callable.")
        if inspect.ismethod(other):
            ref = weakref.WeakMethod(other)
        else:
            ref = weakref.ref(other)
        if ref not in self._funcs:
            self._funcs.append(ref)
        return self

    def __isub__(self, other):
        # is this ok
        for ref in self._funcs:
            obj = ref()
            if obj is other or obj is None:
                self._funcs.remove(ref)
        return self

    def __call__(self, *args, **kwargs):
        dirty = False
        for ref in self._funcs:
            func = ref()
            if func is None:
                dirty = True
                continue
            try:
                r = func(*args, **kwargs)
            except Exception:
                print(f"Ignoring exception in event hook {func}")
                traceback.print_exc()
                continue
            if self.overridable and r is not None:
                return r
        if dirty:
            self.flush()

    def __bool__(self):
        self.flush()
        return bool(self._funcs)

    def flush(self):
        self._funcs = [ref for ref in self._funcs if ref() is not None]


class AsyncEvent(Event):
    def __iadd__(self, other):
        if not inspect.iscoroutinefunction(other):
            raise TypeError("Event handler must be a coroutine.")
        return super().__iadd__(other)

    # todo this is literally the same as Event.__call__ except with async and await instead. Is there a better way?
    async def __call__(self, *args, **kwargs):
        dirty = False
        for ref in self._funcs:
            func = ref()
            if func is None:
                dirty = True
                continue
            try:
                r = await func(*args, **kwargs)
            except Exception:
                print(f"Ignoring exception in event hook {func}")
                traceback.print_exc()
                continue
            if self.overridable and r is not None:
                return r
        if dirty:
            self.flush()


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


def bad_float(*args):
    return any(not math.isfinite(arg) for arg in args)
