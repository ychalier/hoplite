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
        prefix = {
            PlayerMove: "move",
            WalkMove: "walk",
            LeapMove: "leap",
            BashMove: "bash",
            ThrowMove: "throw",
            AltarMove: "altar",
            IdleMove: "idle"
        }[self.__class__]
        if self.target is None:
            return prefix
        return "%s/%d,%d" % (prefix, self.target.x, self.target.y)

    def __str__(self):
        if self.target is None:
            return self.__class__.__name__
        return self.__class__.__name__ + str(self.target)

    @staticmethod
    def from_string(string):
        """Create a `PlayerMove` instance from a representation string.

        Parameters
        ----------
        string : str
            String representing the player move, with the form
            {class}/{target_x},{target_y}.

        Returns
        -------
        PlayerMove
            Corresponding player move. The returned object acutally has the
            class corresponding to its own kind, which inherits from
            `PlayerMove`.

        """
        cls = {
            "move": PlayerMove,
            "walk": WalkMove,
            "leap": LeapMove,
            "bash": BashMove,
            "throw": ThrowMove,
            "altar": AltarMove,
            "idle": IdleMove
        }[string.split("/")[0]]
        target = hoplite.utils.HexagonalCoordinates(
            *tuple(map(int, string.split("/")[1].split(","))))
        return cls(target)

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
                        "Killing with BOMB at %s: %s at %s",
                        bomb_pos,
                        next_state.terrain.demons[neighbor].skill.name,
                        neighbor
                    )
                    if bomb_pos in self._pushed_bombs:
                        # Only kills by knocked bombs count as player kills,
                        # that can be used for the Bloodlust, Surge or
                        # Regeneration prayers.
                        LOGGER.debug("Bomb kills counts as a player kill")
                        self._killed += 1
                    del next_state.terrain.demons[neighbor]
            next_state.terrain.bombs.remove(bomb_pos)
        for demon_pos, demon in next_state.terrain.demons.items():
            demon_damage = demon.attack(next_state, demon_pos)
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
        if self._killed > 0 and\
            (hoplite.game.status.Prayer.SURGE in next_state.status.prayers\
            or hoplite.game.status.Prayer.REGENERATION in next_state.status.prayers):
            next_state.status.spree += 1
            LOGGER.debug("Increasing killing spree, current state: %d", next_state.status.spree)
        else:
            next_state.status.spree = 0
            LOGGER.debug("Resetting killing spree")
        if next_state.status.spree == 3:
            if hoplite.game.status.Prayer.SURGE in next_state.status.prayers:
                LOGGER.debug("Using SURGE")
                next_state.status.restore_energy(100)
                next_state.status.cooldown = 0
                next_state.status.spear = True
                next_state.terrain.spear = None
            elif hoplite.game.status.Prayer.REGENERATION in next_state.status.prayers:
                LOGGER.debug("Using REGENERATION")
                next_state.status.restore_health(1)
            else:
                LOGGER.debug("No prayer to spend killing spree on")
            next_state.status.spree = 0
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

    ENTITY_BOMB = 0
    ENTITY_DEMON = 1

    def _get_bashed_area(self, state):
        bashed_area = {self.target}
        if hoplite.game.status.Prayer.SPINNING_BASH in state.status.prayers:
            bashed_area = hoplite.utils.hexagonal_neighbors(state.terrain.player)
        elif hoplite.game.status.Prayer.SWEEPING_BASH in state.status.prayers:
            bashed_area = {
                self.target,
                self.target + self.target.gradient(state.terrain.player).rotate(-1),
                self.target + self.target.gradient(state.terrain.player).rotate(1),
            }
        LOGGER.debug("Bashed area: %s", bashed_area)
        return bashed_area

    def _push_demon(self, terrain, origin, direction):
        """Make room to push a demon. Exact mechanics are described by the
        original developper [here](https://www.reddit.com/r/Hoplite/comments/fxx69q/).
        Normally, `origin + direction.rotate(-1)` and
        `origin + direction.rotate(1)` are checked in random orders.
        """
        LOGGER.debug("Pushing demon from %s in direction %s", origin, direction)
        candidates = [
            origin + direction,
            origin + direction.rotate(-1),
            origin + direction.rotate(1)
        ]
        LOGGER.debug("Empty tiles candidates: %s", candidates)
        selected = None
        for candidate in candidates:
            if candidate in set(hoplite.utils.SURFACE_COORDINATES)\
                .difference(terrain.demons)\
                .difference([terrain.altar]):
                LOGGER.debug("Found an empty tile at %s", candidate)
                selected = candidate
                break
        if selected is None:
            LOGGER.debug("No empty tile found.")
            if candidates[0] not in hoplite.utils.SURFACE_COORDINATES:
                LOGGER.debug("Forcing escape by crushing the demon out of bound.")
                self._killed += 1
                del terrain.demons[origin]
            else:
                LOGGER.debug("Propagating escape from %s", candidates[0])
                self._push_demon(terrain, candidates[0], direction)
                terrain.demons[candidates[0]] = terrain.demons[origin]
                del terrain.demons[origin]
        else:
            if terrain.surface.get(selected) == hoplite.game.terrain.Tile.MAGMA:
                LOGGER.debug("Escaping into lava, killing.")
                self._killed += 1
            else:
                terrain.demons[selected] = terrain.demons[origin]
            del terrain.demons[origin]

    def _bash_step(self, state, entity, origin, direction):
        target = origin + direction
        LOGGER.debug("Bashing target: %s", target)
        if target == state.terrain.altar:
            LOGGER.debug("Blocked by altar, ending knockback")
            return None
        if target not in hoplite.utils.SURFACE_COORDINATES:
            if entity == BashMove.ENTITY_DEMON:
                LOGGER.debug("Pushing demon out of bound, counts as a kill")
                del state.terrain.demons[origin]
                self._killed += 1
            LOGGER.debug("Knocked out of bound, ending knockback")
            return None
        if entity == BashMove.ENTITY_DEMON\
            and state.terrain.surface.get(target) == hoplite.game.terrain.Tile.MAGMA:
            LOGGER.debug("Pushed demon onto magma kill, ending knockback")
            del state.terrain.demons[origin]
            self._killed += 1
            return None
        if target in state.terrain.demons:
            LOGGER.debug("Bash target is occupied by a demon")
            self._push_demon(state.terrain, target, direction)
        if entity == BashMove.ENTITY_BOMB:
            state.terrain.bombs.remove(origin)
            state.terrain.bombs.add(target)
            self._pushed_bombs.add(target)
        elif entity == BashMove.ENTITY_DEMON:
            state.terrain.demons[target] = state.terrain.demons[origin]
            del state.terrain.demons[origin]
        return target

    def _apply(self, prev_state, next_state):
        for origin in self._get_bashed_area(prev_state):
            if origin in next_state.terrain.bombs:
                entity = BashMove.ENTITY_BOMB
            elif origin in next_state.terrain.demons:
                entity = BashMove.ENTITY_DEMON
            else:
                LOGGER.debug("Nothing to bash at %s", origin)
                continue
            direction = next_state.terrain.player.gradient(origin)
            LOGGER.debug("Bashing %s from %s into %s",
                         ["bomb", "demon"][entity], origin, direction)
            for step in range(next_state.status.attributes.knockback_distance):
                LOGGER.debug("Bashing step %d/%d", step + 1,
                             next_state.status.attributes.knockback_distance)
                target = self._bash_step(next_state, entity, origin, direction)
                if target is None:
                    break
                origin = target
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
