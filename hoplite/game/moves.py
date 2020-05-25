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

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.target == other.target

    def __hash__(self):
        return hash((self.__class__, self.target))

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
        bashed_area = {self.target}
        if hoplite.game.status.Prayer.SPINNING_BASH in prev_state.status.prayers:
            bashed_area = hoplite.utils.hexagonal_neighbors(prev_state.terrain.player)
        elif hoplite.game.status.Prayer.SWEEPING_BASH in prev_state.status.prayers:
            bashed_area = {
                self.target,
                self.target + self.target.gradient(prev_state.terrain.player).rotate(1),
                self.target + self.target.gradient(prev_state.terrain.player).rotate(-1),
            }
        LOGGER.debug("Bashed area: %s", bashed_area)
        for bashed_from in bashed_area:
            # TODO: handle collisions if pushed_to is not an empty tile
            bashed_to = bashed_from + (
                next_state.terrain.player.gradient(bashed_from)
                * next_state.status.attributes.knockback_distance
            )
            if bashed_from in prev_state.terrain.demons:
                if next_state.terrain.surface.get(bashed_to)\
                    in [hoplite.game.terrain.Tile.MAGMA, None]:
                    LOGGER.debug(
                        "Pushed and killed %s from %s to %s",
                        next_state.terrain.demons[bashed_from].skill.name,
                        bashed_from,
                        bashed_to
                    )
                    del next_state.terrain.demons[bashed_from]
                else:
                    next_state.terrain.demons[bashed_to] = next_state.terrain.demons[bashed_from]
                    del next_state.terrain.demons[bashed_from]
            elif bashed_from in prev_state.terrain.bombs:
                next_state.terrain.bombs.remove(bashed_from)
                next_state.terrain.bombs.add(bashed_to)
        next_state.status.cooldown = next_state.status.attributes.cooldown


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
