"""
Base script that implements command handling.

Creator: 10se1ucgo
"""
import sys
import shlex
import inspect
import traceback
import ipaddress
from typing import Dict, Callable

from acelib.constants import CHAT, ENTITY, WEAPON
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from aceserver.types import Entity, ENTITIES
from aceserver.weapons import Weapon, WEAPONS
from acescripts import Script


def command(name=None, aliases=None, admin=False):
    def decorator(func):
        return Command(name or func.__name__, func, aliases, admin)
    return decorator


class NotEnoughArguments(TypeError):
    pass


class IncorrectParameters(TypeError):
    pass


class Command:
    def __init__(self, name: str, func: callable, aliases=None, admin=False):
        self.name = name
        self.func = func
        self.signature = inspect.signature(func)
        self.aliases = aliases or []
        self.admin = admin
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
                        f'Unable to convert argument `{param_name}` "{msg[x]}" to "{param_type}" in command {self.name}'
                    )
            args.append(arg)

        return args


class CommandsScript(Script):
    COMMAND_PREFIX = "/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands: Dict[str, Command] = {}
        self.command_prefix = self.config.get("command_prefix", self.COMMAND_PREFIX)
        self.local_is_admin = self.config.get("local_is_admin", True)
        self.roles = self.config.get("roles", {})

        ServerConnection.try_chat_message += self.try_chat_message
        ServerConnection.on_player_connect += self.on_player_connect
        self.protocol.scripts.on_scripts_loaded += self.on_scripts_loaded

    def add_commands(self, klass):
        for name, command in inspect.getmembers(klass, lambda member: isinstance(member, Command)):
            command.instance = klass
            self.commands[command.name] = command
            for alias in command.aliases:
                self.commands[alias] = command

    def remove_commands(self, klass):
        for command in self.commands.copy().values():
            if command.instance is klass:
                command.instance = None
                for alias in command.aliases:
                    self.commands.pop(alias)
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
            await connection.send_server_message("That command doesn't exist.")
            return False
        if not can_invoke(connection, command):
            await connection.send_server_message("You do not have permission to use that command.")
            return False

        try:
            await command(connection, fragments[1:])
        except Exception:
            await connection.send_server_message(f"Error executing command {command.name}, not enough or malformed arguments")
            print(f"Ignoring error in command {command.name}", file=sys.stderr)
            traceback.print_exc()
        return False

    async def on_player_connect(self, connection: ServerConnection):
        if ipaddress.ip_address(connection.peer.address.host).is_private:
            connection.store["commands_admin"] = True

    @command()
    async def login(self, connection: ServerConnection, password: str):
        if password in self.config.get("admin_passwords", ()):
            connection.store["commands_admin"] = True
            await connection.send_server_message("You logged in as an admin -- all rights granted.")

        for name, options in self.config.get("roles", {}).items():
            if password in options.get("passwords", ()):
                connection.store.setdefault("commands_permissions", set()).update(options.get("permissions", ()))
                await connection.send_server_message(f"You logged in as {name}")

    def on_scripts_loaded(self, scripts):
        for script in scripts.values():
            self.add_commands(script)

    def on_scripts_unloaded(self, scripts):
        for script in scripts.values():
            self.remove_commands(script)

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


def _to_type_from_enum(enum, types, parameter):
    try:
        try:
            type = enum[parameter.upper()]
        except KeyError:
            type = enum(int(parameter))
        return types.get(type)
    except ValueError:
        names = {cls.__name__.lower(): cls for cls in types.values()}
        return names.get(parameter.lower())


@register_converter(Entity)
def to_entity(conn: ServerConnection, parameter: str) -> Entity:
    return _to_type_from_enum(ENTITY, ENTITIES, parameter)


@register_converter(Weapon)
def to_entity(conn: ServerConnection, parameter: str) -> Weapon:
    return _to_type_from_enum(WEAPON, WEAPONS, parameter)


def can_invoke(connection: ServerConnection, command: Command):
    if not command.admin or connection.store.get("commands_admin", False):
        return True

    return command.name in connection.store.get("commands_permissions", ())


def init(protocol: ServerProtocol):
    return CommandsScript(protocol)
