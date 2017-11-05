import shlex
import inspect

from aceserver import protocol, connection
from acescripts import Script


class NotEnoughArguments(TypeError):
    pass


class IncorrectParameters(TypeError):
    pass


class Commands(Script):
    COMMAND_PREFIX = "/"

    def __init__(self, protocol: 'protocol.ServerProtocol', cfg: dict):
        self.protocol = protocol
        self.cfg = cfg

        self.commands = {"setpos": self.setpos, "sethp": self.sethp}
        self.command_prefix = cfg.get("command_prefix", self.COMMAND_PREFIX)

        connection.ServerConnection.try_chat_message += self.try_chat_message

    async def try_chat_message(self, connection: 'connection.ServerConnection', message: str, type: int):
        if not message.startswith(self.command_prefix):
            return

        fragments = shlex.split(message[len(self.command_prefix):])

        command_name = fragments[0]
        command = self.commands.get(command_name)
        if not command:
            return
        try:
            args = self.parse_command(fragments[1:], inspect.signature(command))
        except IndexError:
            raise NotEnoughArguments(f"Not enough commands supplied to {command_name}") from None
        except TypeError as e:
            raise IncorrectParameters(
                f'Unable to convert argument {e.args[0]} "{e.args[1]}" to "{e.args[2]}" in command {command_name}'
            ) from None
        await command(connection, *args)
        return False

    def parse_command(self, arguments: list, signature: inspect.Signature):
        args = []
        parameters = iter(signature.parameters)
        next(parameters) # skip the first argument (the connection that issued the command)
        for x, param_name in enumerate(parameters):
            param: inspect.Parameter = signature.parameters[param_name]
            if param.annotation is param.empty:
                converter = type(param.default) if param.default is not param.empty else str
            else:
                converter = param.annotation

            try:
                arg = converter(arguments[x])
            except IndexError:
                if param.default is param.empty:
                    raise
                arg = param.default
            except (TypeError, ValueError):
                raise IncorrectParameters(param_name, arguments[x], converter)
            args.append(arg)

        return args

    async def setpos(self, connection: 'connection.ServerConnection', x: float, y: float, z: float=None):
        await connection.set_position(x, y, z)

    async def sethp(self, connection: 'connection.ServerConnection', hp: int):
        await connection.set_hp(hp)

    def deinit(self):
        connection.ServerConnection.try_chat_message -= self.try_chat_message


def init(protocol: 'protocol.ServerProtocol', cfg: dict):
    return Commands(protocol, cfg)
