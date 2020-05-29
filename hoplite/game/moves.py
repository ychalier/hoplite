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
    _killed : int
        Number of demons killed during the move resolution
    _pushed_bombs : set[hoplite.utils.HexagonalCoordinates]
        Pushed to positions of bombs that have been knocked by a player Bash.
        When they explode, only knocked bombs will count as player kills, which
        impacts Bloodlust, Surge and Regeneration prayers.

    """

    def __init__(self, target=None):
        self.target = target
        self._killed = 0
        self._pushed_bombs = set()

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.target == other.target

    def __hash__(self):
        return hash((self.__class__, self.target))

    def __repr__(self):
        if self.target is None:
            return self.__class__.__name__
        return self.__class__.__name__ + str(self.target)

    def _apply_damages(self, next_state):
        """Resolve the damage step within the current state.
        """
        damages = 0
        for bomb_pos in list(next_state.terrain.bombs):
            for neighbor in hoplite.utils.hexagonal_neighbors(bomb_pos):
                if neighbor == next_state.terrain.player:
                    LOGGER.debug(
                        "Taking a damage because of BOMB at %s",
                        bomb_pos
                    )
                    damages += 1
                elif neighbor in next_state.terrain.demons:
                    LOGGER.debug(
                        "Killing with BOMB: %s at %s",
                        next_state.terrain.demons[neighbor].skill.name,
                        neighbor
                    )
                    if neighbor in self._pushed_bombs:
                        # Only kills by knocked bombs count as player kills,
                        # that can be used for the Bloodlust, Surge or
                        # Regeneration prayers.
                        self._killed += 1
                    del next_state.terrain.demons[neighbor]
            next_state.terrain.bombs.remove(bomb_pos)
        for demon_pos, demon in next_state.terrain.demons.items():
            demon_damage = demon.attack(self, demon_pos)
            if demon_damage > 0:
                LOGGER.debug(
                    "Taking a damage because of %s at %s",
                    demon.skill.name,
                    demon_pos
                )
            damages += demon_damage
        LOGGER.debug("Total damages received: %d", damages)
        next_state.status.deal_damage(damages)

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
        self._apply_damages(next_state)
        if hoplite.game.status.Prayer.BLOODLUST in next_state.status.prayers:
            next_state.status.restore_energy(self._killed * 6)
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
        if not hoplite.utils.hexagonal_neighbors(next_state.terrain.player)\
            .isdisjoint(prev_state.terrain.demons):
            next_state.status.restore_energy(10)
        self._killed += next_state.apply_attacks(prev_state, [
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
        next_state.status.use_energy(50)
        if not hoplite.utils.hexagonal_neighbors(next_state.terrain.player)\
            .isdisjoint(prev_state.terrain.demons):
            next_state.status.restore_energy(10)
        self._killed += next_state.apply_attacks(prev_state, [
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
            self._killed += 1
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
                    self._killed += 1
                    del next_state.terrain.demons[bashed_from]
                else:
                    next_state.terrain.demons[bashed_to] = next_state.terrain.demons[bashed_from]
                    del next_state.terrain.demons[bashed_from]
            elif bashed_from in prev_state.terrain.bombs:
                self._pushed_bombs.add(bashed_to)
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
