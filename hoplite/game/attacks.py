"""Representation of the attacks performed by the player.
"""

import logging
import hoplite.utils


LOGGER = logging.getLogger(__name__)


class PlayerAttack:
    """Possible attacks that the player can perform.
    Attacks differ from `PlayerMove`.

    Attributes
    ----------
    _killed : int
        Counter for the number of kills resulting from the attack.

    """

    def __init__(self):
        self._killed = 0

    def __repr__(self):
        return self.__class__.__name__

    def _kill(self, next_state, target):
        self._killed += 1
        LOGGER.debug(
            "Killing %s at %s using %s",
            next_state.terrain.demons[target].skill.name,
            target,
            self.__class__.__name__
        )
        del next_state.terrain.demons[target]

    def _apply(self, prev_state, next_state):
        raise NotImplementedError

    def apply(self, prev_state, next_state):
        """Resolve the attack.

        Parameters
        ----------
        prev_state : hoplite.game.state.GameState
            State before the last player move.
        next_state : hoplite.game.state.GameState
            State after the last player move, in which the attacks should be
            performed.

        Returns
        -------
        int
            Number of demons killed during the attack.

        """
        self._apply(prev_state, next_state)
        return self._killed


class Stab(PlayerAttack):  # pylint: disable=R0903
    """Stab attack.
    """

    def _apply(self, prev_state, next_state):
        stabbed = set(hoplite.utils.hexagonal_neighbors(prev_state.terrain.player))\
            .intersection(hoplite.utils.hexagonal_neighbors(next_state.terrain.player))\
            .intersection(prev_state.terrain.demons)
        for target in stabbed:
            self._kill(next_state, target)
        return self._killed


class Lunge(PlayerAttack):  # pylint: disable=R0903
    """Lunge attack.
    """

    def _apply(self, prev_state, next_state):
        if not prev_state.status.spear:
            LOGGER.debug("Lunge impossible because of missing spear")
            return
        target = next_state.terrain.player\
            + prev_state.terrain.player.gradient(next_state.terrain.player)
        if target in next_state.terrain.demons:
            self._kill(next_state, target)
        # TODO: handle deep lunge
