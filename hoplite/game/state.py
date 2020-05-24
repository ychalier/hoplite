"""Gathering of all of the game components.
"""

import enum
import copy
import logging
import hoplite.utils
import hoplite.game.terrain
import hoplite.game.status
import hoplite.game.moves


LOGGER = logging.getLogger(__name__)


@enum.unique
class Interface(enum.Enum):
    """Enumeration of possible game interface displayed on screen.
    """

    EMBARK = 0
    PLAYING = 1
    ALTAR = 2
    FLEECE = 3
    VICTORY = 4
    DEATH = 5


class GameState:
    """Logical representation of a game state.

    Attributes
    ----------
    depth : int
        Current level depth.
    terrain : hoplite.game.terrain.Terrain
        Logical representation of the terrain.
    status : hoplite.game.status.Status
        Logical representation of the player status.

    """

    def __init__(self):
        self.depth = 1
        self.terrain = hoplite.game.terrain.Terrain()
        self.status = hoplite.game.status.Status()

    def __repr__(self):
        return "GameState%s" % self.__dict__

    def copy(self):
        """Copy the current state.

        Returns
        -------
        GameState
            Same state with different address.

        """
        return copy.deepcopy(self)

    def apply_attacks(self, prev_state, attacks):
        """Resolve player attacks.

        Parameters
        ----------
        prev_state : GameState
            State of the game before the last move.
        attacks : list[hoplite.game.attacks.PlayerAttack]
            Player attacks to consider.

        """
        killed = 0
        for atck in attacks:
            killed += atck.apply(prev_state, self)
        # TODO: check for energy restoration procedure
        # TODO: sort attacks in correct resolution order

    def apply_damages(self):
        """Resolve the damage step within the current state.
        """
        damages = 0
        for bomb_pos in list(self.terrain.bombs):
            for neighbor in hoplite.utils.hexagonal_neighbors(bomb_pos):
                if neighbor == self.terrain.player:
                    LOGGER.debug(
                        "Taking a damage because of BOMB at %s",
                        bomb_pos
                    )
                    damages += 1
                elif neighbor in self.terrain.demons:
                    LOGGER.debug(
                        "Killing with BOMB: %s at %s",
                        self.terrain.demons[neighbor].skill.name,
                        neighbor
                    )
                    del self.terrain.demons[neighbor]
            self.terrain.bombs.remove(bomb_pos)
        for demon_pos, demon in self.terrain.demons.items():
            demon_damage = demon.attack(self, demon_pos)
            if demon_damage > 0:
                LOGGER.debug(
                    "Taking a damage because of %s at %s",
                    demon.skill.name,
                    demon_pos
                )
            damages += demon_damage
        LOGGER.debug("Total damages received: %d", damages)
        self.status.deal_damage(damages)

    def possible_moves(self):
        """Enumerates all possible moves for the player in the current state.

        Returns
        -------
        Iterator[hoplite.game.moves.PlayerMove]
            Legal moves for the player in the current game state.

        """
        def cannot_land_on(pos):
            return (self.terrain.surface.get(pos) == hoplite.game.terrain.Tile.MAGMA)\
                or (pos == self.terrain.altar)\
                or (pos in self.terrain.bombs)\
                or (pos in self.terrain.demons)
        for pos in hoplite.utils.hexagonal_neighbors(self.terrain.player):
            if cannot_land_on(pos):
                continue
            yield hoplite.game.moves.WalkMove(pos)
        if self.status.can_leap():
            for pos in hoplite.utils\
                    .hexagonal_circle(
                            self.terrain.player,
                            self.status.attributes.leap_distance)\
                    .difference(hoplite.utils.hexagonal_circle(self.terrain.player, 1)):
                if cannot_land_on(pos):
                    continue
                yield hoplite.game.moves.LeapMove(pos)
        if self.status.can_bash():
            for pos in hoplite.utils.hexagonal_neighbors(self.terrain.player):
                yield hoplite.game.moves.BashMove(pos)
        if self.status.can_throw():
            for pos in hoplite.utils.hexagonal_circle(
                    self.terrain.player,
                    self.status.attributes.throw_distance):
                if (self.terrain.surface.get(pos) == hoplite.game.terrain.Tile.MAGMA)\
                        or (pos == self.terrain.altar)\
                        or (pos in self.terrain.bombs):
                    continue
                yield hoplite.game.moves.ThrowMove(pos)
        if self.terrain.altar_prayable\
                and self.terrain.altar in hoplite.utils.hexagonal_neighbors(self.terrain.player):
            yield hoplite.game.moves.AltarMove(self.terrain.altar)


class LostGameException(Exception):
    """
    Exception to be raised when the game is lost.
    """


class AltarState:  # pylint: disable=R0903
    """Represent the state of an Altar.

    Attributes
    ----------
    prayers : dict[hoplite.game.status.Prayer, int]
            Prayers available at the altar, and their observed height
            (in pixels).

    """

    def __init__(self):
        self.prayers = dict()

    def __str__(self):
        return str(list(self.prayers.keys()))
