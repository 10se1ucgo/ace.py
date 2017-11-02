from typing import Generator

from acelib.constants import *
from aceserver import protocol, connection, entity

class Team(object):
    def __init__(self, team_id: TeamType, name: str, color: tuple, spectator: bool, protocol: 'protocol.ServerProtocol'):
        self.id = team_id
        self.name = name
        self.color = color
        self.spectator = spectator
        self.protocol = protocol

        self.other: 'Team' = None

        self.score = 0
        self.kills = 0

    def players(self) -> Generator['connection.ServerConnection', None, None]:
        for conn in self.protocol.players.values():
            if conn.player.team == self:
                yield conn

    def entities(self) -> Generator['entity.Entity', None, None]:
        for ent in self.protocol.entities.values():
            if ent.team == self:
                yield ent

    def __str__(self):
        return f"{self.name} team"

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id!r}, name={self.name}, color={self.color})>"
