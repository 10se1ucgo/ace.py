import asyncio
import random
from typing import *

import enet

from acelib.constants import *
from acelib.math3d import Vector3
from acemodes import GameMode
from aceserver import protocol, connection, types
from aceserver.loaders import progress_bar


class Territory(types.CommandPost):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._progress = float(self.team.id) if self.team is not None else 0.5
        self._rate = 0
        self.players = []

    def update(self, dt):
        if self.destroyed:
            return
        self.do_gravity()
        self.get_players()

        self.progress += self.rate * dt

    def get_players(self):
        old = self.players.copy()
        self.players.clear()
        for ply in self.protocol.players.values():
            if ply.dead: continue

            dist = self.position.sq_distance(ply.position)
            if dist <= TC_CAPTURE_DISTANCE ** 2:
                self.players.append(ply)

        if self.players != old:
            # Stop showing the progress bar to players that left
            left = set(old) - set(self.players)
            progress_bar.stopped = True
            self.protocol._broadcast_loader(progress_bar.generate(), connections=left)

        if not old and self.players:
            capturing = self.protocol.team1 if self.rate < 0 else self.protocol.team2
            msg = f"{capturing.name} team is capturing {self.get_grid()}"
            self.protocol.loop.create_task(self.protocol.broadcast_hud_message(msg))

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        value = max(0.0, min(1.0, value))
        if value == self._progress:
            return
        self._progress = value

        team = None
        if self._progress == 0.0:
            team = self.protocol.team1
        elif self._progress == 1.0:
            team = self.protocol.team2
        if team == self.team:
            return
        self.protocol.loop.create_task(self.set_team(team))

    async def set_team(self, team: types.Team=None):
        if team is not None:
            await self.protocol.broadcast_hud_message(f"{team.name} team captured {self.get_grid()}")
        await super().set_team(team)

    @property
    def rate(self):
        rate = sum(-1 if ply.team is self.protocol.team1 else 1 for ply in self.players) * TC_CAPTURE_RATE
        self.rate = rate
        return rate

    @rate.setter
    def rate(self, value):
        if value == self._rate:
            return
        self._rate = value
        self.send_progress_bar()

    def send_progress_bar(self):
        progress_bar.set(self.progress, self.rate)
        progress_bar.color1.rgb = self.protocol.team1.color
        progress_bar.color2.rgb = self.protocol.team2.color
        self.protocol._broadcast_loader(progress_bar.generate(), connections=self.players)

    def get_grid(self):
        x, y, z = self.position.xyz
        letter = chr(ord('A') + int(x / 64))
        number = int(y / 64) + 1
        return f"{letter}{number}"


class TC(GameMode):
    name = "TC"
    score_limit = 0

    async def init(self):
        await super().init()
        self.territories: Dict[int, Territory] = {}
        await self.spawn_ents()

    async def spawn_ents(self):
        # Limit to middleish area of the map.
        l = self.protocol.map.length()
        y1 = l * (3 / 8)
        y2 = l * (5 / 8)

        # Max distance between each point
        interval = self.protocol.map.width() / MAX_TERRITORY_COUNT
        for x in range(MAX_TERRITORY_COUNT):
            position = self.protocol.map.get_random_pos(interval * x, y1, interval * (x + 1), y2)

            team = None
            if x < MAX_TERRITORY_COUNT // 2:
                team = self.protocol.team1
            elif x > (MAX_TERRITORY_COUNT - 1) // 2:
                team = self.protocol.team2

            cp = await self.protocol.create_entity(Territory, position, team)
            self.territories[cp.id] = cp

    async def deinit(self):
        for ent in self.territories.values(): ent.destroy()
        self.territories.clear()
