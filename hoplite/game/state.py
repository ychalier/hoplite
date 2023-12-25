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
    STAIRS = 6
    BLACK = 7


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
        return "%d;%s;%s" % (self.depth, repr(self.terrain), repr(self.status))

    def __str__(self):
        return "GameState%s" % self.__dict__

    def __eq__(self, other):
        return (self.depth == other.depth
                and self.terrain == other.terrain
                and self.status == other.status)

    def __hash__(self):
        return hash(self.depth + hash(self.terrain) + hash(self.status))

    @classmethod
    def from_string(cls, string):
        """Create and return a `GameState` object from its string representation.

        Parameters
        ----------
        string : str
            String representation of the game state, composed of three parts
            separated by semicolons. First part is an integer corresponding to
            the current depth. Second part is the string representation of the
            `hoplite.game.terrain.Terrain`. Last part is the string
            representation of the `hoplite.game.status.Status`.

        Returns
        -------
        GameState
            Game state corresponding to that state.

        """
        state = cls()
        depth, terrain_string, status_string = string.split(";")
        state.depth = int(depth)
        state.terrain = hoplite.game.terrain.Terrain.from_string(terrain_string)
        state.status = hoplite.game.status.Status.from_string(status_string)
        return state

    def copy(self):
        """Copy the current state.

        Returns
        -------
        GameState
            Same state with different address.

        """
        return copy.deepcopy(self)

    def update(self, new_state):
        """Update the current state with a newly parsed one.

        Parameters
        ----------
        new_state : GameState
            New game state, recently parsed.

        """
        self.depth = new_state.depth
        self.terrain = new_state.terrain
        self.status.update(new_state.status)

    def apply_attacks(self, prev_state, attacks):
        """Resolve player attacks.

        Parameters
        ----------
        prev_state : GameState
            State of the game before the last move.
        attacks : list[hoplite.game.attacks.PlayerAttack]
            Player attacks to consider.

        Rerturns
        --------
        int
            Total number of demons killed by the attacks.

        """
        killed = 0
        for atck in attacks:
            killed += atck.apply(prev_state, self)
        return killed

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
        # FIXME: disabled AltarMoves to avoid crash on prayers detection
        # if self.terrain.altar_prayable\
        #         and self.terrain.altar in hoplite.utils.hexagonal_neighbors(self.terrain.player):
        #     yield hoplite.game.moves.AltarMove(self.terrain.altar)
        if hoplite.game.status.Prayer.PATIENCE in self.status.prayers:
            yield hoplite.game.moves.IdleMove(self.terrain.player)


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

    def __repr__(self):
        return ",".join([str(prayer.value) for prayer in self.prayers])

    def __str__(self):
        return str(list(self.prayers.keys()))
