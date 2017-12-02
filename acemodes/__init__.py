import importlib
from typing import Tuple

from acelib import constants
from aceserver import protocol, connection, types, util


class GameMode:
    name: str = "Default"

    @property
    def score_limit(self) -> int:
        return self.config.get("score_limit", 10)

    def __init__(self, protocol: 'protocol.ServerProtocol'):
        self.protocol = protocol
        self.config = protocol.config.get("modes.default")
        module_name = ''.join(str(self.__module__).split(".")[1:])  # strip package name
        self.config.update(protocol.config.get("modes." + module_name, {}))

    async def init(self):
        # TODO should this be in the base GameMode or should this just be default behaviour within these classes?
        types.HealthCrate.on_collide += self.on_health_crate
        types.AmmoCrate.on_collide += self.on_ammo_crate
        connection.ServerConnection.on_player_kill += self.on_player_kill

        self.win_sound = self.protocol.create_sound("horn")

    async def deinit(self):
        pass

    async def reset(self, winner: types.Team=None):
        self.protocol.loop.create_task(self.on_game_end(winner))
        if winner is not None:
            await self.win_sound.play()
            await self.protocol.broadcast_hud_message(f"{winner.name} team wins!")
        await self.deinit()
        await self.init()
        for player in self.protocol.players.values():
            await player.spawn()
        for team in self.protocol.teams.values():
            team.reset()

    def check_win(self):
        if any(team.score == self.score_limit for team in self.protocol.teams.values()):
            winner = max(self.protocol.teams.values(), key=lambda team: team.score)
            self.protocol.loop.create_task(self.reset(winner))

    def update(self, dt: float):
        pass

    async def on_health_crate(self, crate: types.HealthCrate, connection: 'connection.ServerConnection'):
        await connection.set_hp(100)
        crate.destroy()

    async def on_ammo_crate(self, crate: types.AmmoCrate, connection: 'connection.ServerConnection'):
        connection.weapon.restock()
        await connection.weapon.send_ammo()
        crate.destroy()

    async def on_player_kill(self, player: 'connection.ServerConnection', kill_type: constants.KILL, killer: 'connection.ServerConnection'):
        if not killer or killer is player:
            # suicide
            player.score -= 1
        else:
            killer.score += 1

    def get_spawn_point(self, player: 'connection.ServerConnection') -> Tuple[int, int, int]:
        x, y, z = self.get_random_pos(player.team)
        return x + 0.5, y + 0.5, z - 2

    def get_random_pos(self, team) -> Tuple[int, int, int]:
        sections = self.protocol.map.width() / 8
        offset = team.id * (self.protocol.map.width() - (sections * 2))
        x, y, z = self.protocol.map.get_random_pos(0 + offset, 0, (sections * 2) + offset, self.protocol.map.width())
        return x, y, z

    # Hooks
    on_game_end = util.AsyncEvent()


def get_game_mode(protocol: 'protocol.ServerProtocol', mode_name: str):
    module = importlib.import_module(f"acemodes.{mode_name}")
    mode = module.init(protocol)
    if not isinstance(mode, GameMode):
        raise TypeError(f"Mode {mode_name} did not return a GameMode instance!")
    return mode
