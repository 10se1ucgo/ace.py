# its an EXAMPLE
from aceserver import protocol, connection


class CensorScript:
    def __init__(self, protocol: 'protocol.ServerProtocol', cfg: dict):
        self.bad_words = ["fuck", "piss", "shit", "cunt"] + cfg.get("bad_words", [])
        self.really_bad_words = ["faggot"] + cfg.get("really_bad_words", [])
        # TODO find a cleaner way to have this
        connection.ServerConnection.on_chat_message += self.censor

    async def censor(self, connection: 'connection.ServerConnection', message: str, type: int):
        if any(really_bad_word in message for really_bad_word in self.really_bad_words):
            return False

        for bad_word in self.bad_words:
            message = message.replace(bad_word, "*" * len(bad_word))
        return message


def init(protocol: 'protocol.ServerProtocol', cfg: dict):
    # TODO protocol should probably hold references to the scripts it has loaded.
    CensorScript(protocol, cfg)
