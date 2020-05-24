"""Representation of possible player moves.
"""

import logging
import hoplite.game.attacks
import hoplite.game.terrain


LOGGER = logging.getLogger(__name__)


class PlayerMove:
    """Abstract class for possible player moves.

    Parameters
    ----------
    target : hoplite.utils.HexagonalCoordinates
        Target tile for moves requiring it, `None` otherwise.

    Attributes
    ----------
    target

    """

    def __init__(self, target=None):
        self.target = target

    def __repr__(self):
        if self.target is None:
            return self.__class__.__name__
        return self.__class__.__name__ + str(self.target)

    def apply(self, prev_state):
        """Perform the move: move entities, check for enemies killed or knocked
        and damage taken. Enemy movements are not taken into account.

        Parameters
        ----------
        prev_state : hoplite.game.state.GameState
            The state of the game before performing the move.

        Returns
        -------
        hoplite.game.state.GameState
            The next state of the game after performing the move.

        """
        next_state = prev_state.copy()
        self._apply(prev_state, next_state)
        next_state.apply_damages()
        return next_state

    def _apply(self, prev_state, next_state):
        raise NotImplementedError


class WalkMove(PlayerMove):  # pylint: disable=R0903
    """Player walks to an adjacent tile.
    """

    def _apply(self, prev_state, next_state):
        next_state.terrain.player = self.target
        if self.target == next_state.terrain.spear:
            next_state.status.spear = True
            next_state.terrain.spear = None
        next_state.apply_attacks(prev_state, [
            hoplite.game.attacks.Stab(),
            hoplite.game.attacks.Lunge()
        ])


class LeapMove(PlayerMove):  # pylint: disable=R0903
    """Player jumps to a separated tile.
    """

    def _apply(self, prev_state, next_state):
        next_state.terrain.player = self.target
        if self.target == next_state.terrain.spear:
            next_state.status.spear = True
            next_state.terrain.spear = None
        next_state.status.energy -= 50
        # TODO: check for stunned if there is the ability for it
        next_state.apply_attacks(prev_state, [
            hoplite.game.attacks.Stab(),
            hoplite.game.attacks.Lunge()
        ])


class ThrowMove(PlayerMove):  # pylint: disable=R0903
    """Player throws spear.
    """

    def _apply(self, prev_state, next_state):
        next_state.status.spear = False
        if self.target in next_state.terrain.demons:
            LOGGER.debug(
                "Killing %s with spear",
                next_state.terrain.demons[self.target].skill.name
            )
            del next_state.terrain.demons[self.target]
        next_state.status.spear = False
        next_state.terrain.spear = self.target


class BashMove(PlayerMove):  # pylint: disable=R0903
    """Player bashes a tile.
    """

    def _apply(self, prev_state, next_state):
        # TODO: handle arc/circle
        # TODO: handle knockback distance
        # TODO: handle collisions (and pushed sideways)
        pushed_to = self.target + \
            next_state.terrain.player.gradient(self.target)
        if self.target in prev_state.terrain.demons:
            if pushed_to not in next_state.terrain.surface:
                LOGGER.debug(
                    "Pushed %s at %s out of bound",
                    next_state.terrain.demons[self.target].skill.name,
                    self.target
                )
                del next_state.terrain.demons[self.target]
            elif next_state.terrain.surface[pushed_to] == hoplite.game.terrain.Tile.MAGMA:
                LOGGER.debug(
                    "Pushed %s at %s into magma",
                    next_state.terrain.demons[self.target].skill.name,
                    self.target
                )
                del next_state.terrain.demons[self.target]
            else:
                next_state.terrain.demons[pushed_to] = next_state.terrain.demons[self.target]
                del next_state.terrain.demons[self.target]
        if self.target in next_state.terrain.bombs:
            next_state.terrain.bombs.remove(self.target)
            next_state.terrain.bombs.add(pushed_to)
        # TODO: set appropriate cooldown value
        next_state.status.cooldown = 4


class IdleMove(PlayerMove):  # pylint: disable=R0903
    """Player uses the `hoplite.game.status.Prayer.PATIENCE` prayer.
    """

    def _apply(self, prev_state, next_state):
        pass


class AltarMove(PlayerMove):  # pylint: disable=R0903
    """Player prays at the altar.
    """

    def _apply(self, prev_state, next_state):
        next_state.terrain.altar_prayable = False
