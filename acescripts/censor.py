"""
Basic example of a script

Creator: 10se1ucgo
"""
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from acescripts import Script


class CensorScript(Script):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bad_words = ["fuck", "piss", "shit", "cunt"] + self.config.get("bad_words", [])
        self.really_bad_words = ["faggot"] + self.config.get("really_bad_words", [])
        # TODO find a cleaner way to have this
        ServerConnection.try_chat_message += self.censor

    def censor(self, connection: ServerConnection, message: str, type: int):
        if any(really_bad_word in message for really_bad_word in self.really_bad_words):
            # returning False completely cancels the hook, and prevents the message from being sent
            connection.send_server_message(f"Watch your profanity, {connection.name}!")
            return False

        for bad_word in self.bad_words:
            message = message.replace(bad_word, "*" * len(bad_word))
        # returning message cancels all further hooks, but replaces the message with our own version.
        return message


def init(protocol: ServerProtocol):
    return CensorScript(protocol)
