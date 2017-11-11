"""
Basic example of a script

Creator: 10se1ucgo
"""
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from acescripts import Script


class CensorScript(Script):
    def __init__(self, protocol: ServerProtocol, cfg: dict):
        super().__init__(protocol, cfg)
        self.bad_words = ["fuck", "piss", "shit", "cunt"] + cfg.get("bad_words", [])
        self.really_bad_words = ["faggot"] + cfg.get("really_bad_words", [])
        # TODO find a cleaner way to have this
        ServerConnection.try_chat_message += self.censor

    async def censor(self, connection: ServerConnection, message: str, type: int):
        if any(really_bad_word in message for really_bad_word in self.really_bad_words):
            # returning False completely cancels the hook, and prevents the message from being sent
            await connection.send_server_message(f"Watch your profanity, {connection.name}!")
            return False

        for bad_word in self.bad_words:
            message = message.replace(bad_word, "*" * len(bad_word))
        # returning message cancels all further hooks, but replaces the message with our own version.
        return message


def init(protocol: ServerProtocol, cfg: dict):
    return CensorScript(protocol, cfg)
