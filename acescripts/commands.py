"""
Base script that implements command handling. Doesn't do anything on its own.

Creator: 10se1ucgo
"""
import sys
import shlex
import inspect
import traceback
from typing import Dict, Callable

from acelib.constants import CHAT
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from acescripts import Script


class NotEnoughArguments(TypeError):
    pass


class IncorrectParameters(TypeError):
    pass


class Command:
    def __init__(self, name: str, func: callable):
        self.name = name
        self.func = func
        self.signature = inspect.signature(func)
        self.instance = None

    def __call__(self, connection: ServerConnection, msg: list):
        if self.instance is not None:
            return self.func(self.instance, connection, *self.parse_command(connection, msg))
        return self.func(connection, *self.parse_command(connection, msg))

    def parse_command(self, connection: ServerConnection, msg: list) -> list:
        args = []

        parameters = iter(self.signature.parameters)
        if self.instance is not None:
            next(parameters)  # skip the self argument (the script that owns the command)
        next(parameters) # skip the connection argument (the connection that issued the command)

        for x, param_name in enumerate(parameters):
            param: inspect.Parameter = self.signature.parameters[param_name]
            if param.annotation is param.empty:
                param_type = type(param.default) if param.default is not param.empty else str
            else:
                param_type = param.annotation

            converter = _converters.get(param_type)
            try:
                arg = msg[x]
            except IndexError:
                if param.default is param.empty:
                    raise NotEnoughArguments(f"Not enough commands supplied to {self.name}") from None
                arg = param.default
            else:
                try:
                    if converter:
                        arg = converter(connection, arg)
                    else:
                        arg = param_type(arg)
                except (TypeError, ValueError):
                    raise IncorrectParameters(
                        f'Unable to convert argument {param_name} "{msg[x]}" to "{param_type}" in command {self.name}'
                    )
            args.append(arg)

        return args


class CommandsScript(Script):
    COMMAND_PREFIX = "/"

    def __init__(self, protocol: ServerProtocol, cfg: dict):
        super().__init__(protocol, cfg)
        self.commands: Dict[str, Command] = {}
        self.command_prefix = cfg.get("command_prefix", self.COMMAND_PREFIX)

        ServerConnection.try_chat_message += self.try_chat_message

    def add_commands(self, klass):
        for name, command in inspect.getmembers(klass, lambda member: isinstance(member, Command)):
            command.instance = klass
            self.commands[command.name] = command

    def remove_commands(self, klass):
        for command in self.commands.copy().values():
            if command.instance is klass:
                command.instance = None
                self.commands.pop(command.name)

    async def try_chat_message(self, connection: ServerConnection, message: str, type: CHAT):
        if not message.startswith(self.command_prefix):
            return

        fragments = shlex.split(message[len(self.command_prefix):])
        if not fragments:
            return

        command_name = fragments[0]
        command = self.commands.get(command_name)
        if not command:
            return

        try:
            await command(connection, fragments[1:])
        except Exception:
            print(f"Ignoring error in command {command.name}", file=sys.stderr)
            traceback.print_exc()
        return False


_converters: Dict[str, Callable] = {}
def register_converter(param_type):
    def decorator(func):
        _converters[param_type] = func
        return func
    return decorator


@register_converter(ServerConnection)
def to_connection(conn: ServerConnection, parameter: str) -> ServerConnection:
    ply = conn.protocol.get_ply_by_name(parameter)
    if not ply:
        ply = conn.protocol.players.get(int(parameter.lstrip("#")))
    return ply


# TODO permissions
def command(name=None):
    def decorator(func):
        return Command(name or func.__name__, func)
    return decorator


def init(protocol: ServerProtocol, cfg: dict):
    return CommandsScript(protocol, cfg)
