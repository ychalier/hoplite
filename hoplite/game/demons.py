"""Representation of the demons, the enemies of the game.
"""

import enum
import hoplite.utils


@enum.unique
class DemonSkill(enum.Enum):
    """
    Enumeration of demon skills.
    """

    FOOTMAN = 0
    ARCHER = 1
    DEMOLITIONIST = 2
    WIZARD = 3


class Demon:  # pylint: disable=R0903
    """Representation of a demon, a resident of the Underworld.

    Parameters
    ----------
    skill : DemonSkill
        Type of Demon.
    min_range : int
        Minimum attack range.
    max_range : int
        Maximum attack range.
    careful : bool
        Whether to ignore attack direction where another demon could be hit.

    """

    def __init__(self, skill, min_range=0, max_range=0, careful=False):
        self.skill = skill
        self.min_range = min_range
        self.max_range = max_range
        self.careful = careful

    def range(self, terrain, demon_pos):
        """Compute the set of positions a range demon can reach with an attack,
        in all 6 hexagonal directions, taking into account obstruction from
        altars and other demons, as well as minimum and maximum range.

        Parameters
        ----------
        terrain : hoplite.game.terrain.Terrain
            Terrain of the current position.
        demon_pos : hoplite.utils.HexagonalCoordinates
            Location of the demon to compute the range of.

        Returns
        -------
        set[hoplite.utils.HexagonalCoordinates]
            Positions that can be attacked by the demon in the current state.

        """
        targets = set()
        for direction in hoplite.utils.HEXAGONAL_DIRECTIONS:
            line_targets = set()
            line = hoplite.utils.hexagonal_line(demon_pos, direction)[1:]
            for dist, pos in enumerate(line):
                if self.min_range <= dist < self.max_range:
                    line_targets.add(pos)
                if dist == self.max_range - 1\
                    or pos == terrain.altar\
                    or pos in terrain.demons:
                    break
            if not self.careful\
                or len(line_targets.intersection(terrain.demons)) == 0:
                targets = targets.union(line_targets)
        return targets.intersection(hoplite.utils.SURFACE_COORDINATES)

    def attack(self, game_state, demon_pos):
        """Resolve the attack of the demon.

        Parameters
        ----------
        game_state : hoplite.game.state.GameState
            Game state in which the attack occurs.
        demon_pos : hoplite.utils.HexagonalCoordinates
            Position of the demon attacking.

        Returns
        -------
        int
            Damage inflicted by the demon to the player.

        """
        raise NotImplementedError


class Footman(Demon):  # pylint: disable=R0903
    """
    Footman demon. Attacks when adjacent to the player.
    """

    def __init__(self):
        Demon.__init__(self, DemonSkill.FOOTMAN)

    def attack(self, game_state, demon_pos):
        if demon_pos in hoplite.utils.hexagonal_neighbors(game_state.terrain.player):
            return 1
        return 0


class Archer(Demon):  # pylint: disable=R0903
    """
    Archer demon. Shoots arrows.
    """

    def __init__(self):
        Demon.__init__(self, DemonSkill.ARCHER, 1, 5, False)

    def attack(self, game_state, demon_pos):
        if game_state.terrain.player in self.range(game_state.terrain, demon_pos):
            return 1
        return 0


class Demolitionist(Demon):  # pylint: disable=R0903
    """
    Demolitionist demon. Throws bombs.
    """

    def __init__(self, holds_bomb=False):
        Demon.__init__(self, DemonSkill.DEMOLITIONIST)
        self.holds_bomb = holds_bomb
        self.cooldown = 0

    def attack(self, game_state, demon_pos):
        self.cooldown = max(0, self.cooldown - 1)
        # TODO: proper cooldown handling
        return 0


class Wizard(Demon):  # pylint: disable=R0903
    """
    Wizard demon. Uses magic wand.
    """

    def __init__(self, charged_wand=True):
        Demon.__init__(self, DemonSkill.WIZARD, 0, 5, True)
        self.charged_wand = charged_wand

    def attack(self, game_state, demon_pos):
        # TODO: proper cooldown handling
        if game_state.terrain.player in self.range(game_state.terrain, demon_pos):
            self.charged_wand = False
            return 1
        self.charged_wand = True
        return 0
