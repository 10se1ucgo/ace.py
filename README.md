very wip

its a LEARNING EXPERIENCE so pls dont flame

feedback and help very welcome!!!

# RUNNING

1. build
2. edit config.json
3. run run.py

# BUILDING

You'll need
 * Python 3.6+
 * pyenet
 * Cython
 * A working C++(11?) compiler.
    * If you're on Windows you'll want to use MSVC 2015 or 2017
    (should be the same MSVC version your Python installation was built with)

See `build.bat` for an example on building.

OPTIONAL:
 * uvloop

# STUFF AND THINGS (eventually will be a TODO)
 * Protocol:
    * [x] Script loading/unloading
      * [x] Scripted gamemodes.
      * [x] Built-in command script with argument parser etc.
      * [ ] Complete set of hooks and utility functions
      * [ ] Default set of general server scripts
    * [x] Map loading and iterative sending
      * [ ] Map switching/rotations
      * [ ] Map metadata
      * [ ] Proper configuration
    * [x] Server packs (models, sounds, etc.)
    * [x] Dynamic entities
    * [x] Sounds played by server
    * [x] System chat messages (big hud messages too)
 * Connection:
    * All these packets sent by the client are currently handled by the server:
      * PositionOrientationData (update data for rubberbanding and orientation)
      * InputData (movement directions + jump crouch sneak sprint)
      * ExistingPlayer (player join + set name/team/weapon)
        * spectator included \[untested\]
      * ChatMessage (chat messages, team/global :P)
      * BlockAction (building, destroying blocks)
      * BlockLine
      * WeaponInput/Reload (primary/secondary fire, reload)
      * ChangeClass/Team (weapon/team)
      * SetTool/Color (current selected tool/block color)
      * UseOrientedItem (grenade thrown or rpg fired)
      * HitPacket (weapon fire hits)
      * PlaceMG (places a mounted machine gun at target location)
      * UseCommand (generic use button keypress)
    * [x] Basic rapid hack prevention
 * Gameplay
    * [x] Rifle, SMG, Shotgun, RPG, Sniper and basic MG support
    * [x] Grenades and Rockets.
    * [x] Building and destroying
    * [x] Spawning, dying, respawning
 * [x] probably some other things
 * [ ] probably another set of other things

# License
I hope I did this right.
```
Copyright (C) 10se1ucgo 2017
based on pyspades <https://github.com/infogulch/pyspades> (C) Mathias Kaerlev 2011-2012.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
