import asyncio
import random
from typing import *

import enet

from acelib.constants import *
from acelib.math3d import Vector3
from acemodes import GameMode
from aceserver import protocol, connection, types, util
from aceserver.loaders import progress_bar


class Territory(types.CommandPost):
    on_start_capture = util.AsyncEvent()
    on_captured = util.AsyncEvent()

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
                # there werent any players on it last update but there are now
                # TODO this isnt the best way
                capturing = self.protocol.team1 if self.rate < 0 else self.protocol.team2
                self.protocol.loop.create_task(self.on_start_capture(self, capturing))

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        value = max(0.0, min(1.0, value))
        if value == self._progress:
            return

        team = False
        if value == 0.0:
            team = self.protocol.team1
        elif value == 1.0:
            team = self.protocol.team2
        elif self._progress <= 0.5 <= value:
            team = None

        self._progress = value

        if team is not False and team != self.team:
            self.protocol.loop.create_task(self.set_team(team))

    async def set_team(self, team: types.Team=None):
        await super().set_team(team)
        await self.on_captured(self, team)

    @property
    def rate(self):
        rate = sum(-1 if ply.team is self.protocol.team1 else 1 for ply in self.players) * TC_CAPTURE_RATE
        if rate != self._rate:
            self.send_progress_bar(rate)
        self._rate = rate
        return rate

    def send_progress_bar(self, rate):
        progress_bar.set(self._progress, rate)
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
    score_limit = MAX_TERRITORY_COUNT

    async def init(self):
        await super().init()
        Territory.on_captured = self.on_territory_captured
        Territory.on_start_capture = self.on_territory_start_capture

        self.territories: List[Territory] = []
        await self.spawn_ents()
        self.update_scores()

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
            self.territories.append(cp)

    async def deinit(self):
        for ent in self.territories: ent.destroy()
        self.territories.clear()

    async def reset(self, winner: types.Team=None):
        if winner is not None:
            await self.protocol.broadcast_hud_message(f"{winner.name} team wins!")
        await self.deinit()
        await self.init()

    def update_scores(self):
        self.protocol.team1.score = len([t for t in self.territories if t.team is self.protocol.team1])
        self.protocol.team2.score = len([t for t in self.territories if t.team is self.protocol.team2])
        self.check_win()

    async def on_territory_captured(self, territory: Territory, capturing: types.Team):
        grid = self.protocol.map.to_grid(territory.position.x, territory.position.y)
        msg = f"{capturing.name} team captured {grid}" if capturing is not None else f"{grid} has been neutralized"
        await self.protocol.broadcast_hud_message(msg)
        self.update_scores()

    async def on_territory_start_capture(self, territory: Territory, capturing: types.Team):
        grid = self.protocol.map.to_grid(territory.position.x, territory.position.y)
        await self.protocol.broadcast_hud_message(f"{capturing.name} team is capturing {grid}")
