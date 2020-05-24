"""Game AI components.
"""

import logging
import numpy
import hoplite.game.demons
import hoplite.game.status

LOGGER = logging.getLogger(__name__)


class Brain:
    """Brain central unit: makes decisions.

    Attributes
    ----------
    demon_weights : dict[hoplite.game.demons.DemonSkill, float]
        Estimated dangerosity of demons.
    weights : numpy.ndarray
        Vector with the weights for the game state features.
    logger : logging.Logger
        Logger to write debug information.

    """

    def __init__(self):
        self.demon_weights = {
            hoplite.game.demons.DemonSkill.FOOTMAN: 1,
            hoplite.game.demons.DemonSkill.DEMOLITIONIST: 2,
            hoplite.game.demons.DemonSkill.ARCHER: 3,
            hoplite.game.demons.DemonSkill.WIZARD: 4
        }
        self.weights = numpy.array([
            -100,  # being dead is very bad
            10,
            .5,
            1,
            -.5,
            -5,
            -1,
            -1.24,  # praying is good (losing 1 heart costs 1.25)
        ])
        self.prayer_weights = {
            hoplite.game.status.Prayer.DIVINE_RESTORATION: 0,
            hoplite.game.status.Prayer.FORTITUDE: 1,
            hoplite.game.status.Prayer.BLOODLUST: 1,
            hoplite.game.status.Prayer.MIGHTY_BASH: 3,
            hoplite.game.status.Prayer.SWEEPING_BASH: 3,
            hoplite.game.status.Prayer.SPINNING_BASH: 3,
            hoplite.game.status.Prayer.QUICK_BASH: 3,
            hoplite.game.status.Prayer.GREATER_THROW: 3,
            hoplite.game.status.Prayer.GREATER_THROW_II: 2,
            hoplite.game.status.Prayer.GREATER_ENERGY: 3,
            hoplite.game.status.Prayer.GREATER_ENERGY_II: 2,
            hoplite.game.status.Prayer.DEEP_LUNGE: 5,
            hoplite.game.status.Prayer.PATIENCE: 1,
            hoplite.game.status.Prayer.SURGE: -1,
            hoplite.game.status.Prayer.REGENERATION: -1,
            hoplite.game.status.Prayer.WINGED_SANDALS: 2,
            hoplite.game.status.Prayer.STAGGERING_LEAP: -1,
        }
        # self.logger = logging.getLogger("brain")

    def extract(self, game_state):
        """Extract features of a game state. Values are manually scaled to
        remain around [0, 1].

        Parameters
        ----------
        game_state : hoplite.game.state.GameState
            State to extract the features of.

        Returns
        -------
        numpy.ndarray
            Vector with extracted features.

        """
        path = game_state.terrain.pathfind(
            game_state.terrain.player,
            game_state.terrain.stairs
        )
        if path is None:
            path_length = 20
        else:
            path_length = len(path)
        features = [
            int(game_state.status.health == 0),  # from 0 to 1
            .125 * game_state.status.health,  # from 0 to 8
            int(game_state.status.spear),  # from 0 to 1
            .01 * game_state.status.energy,  # usually around 100, but possibly above
            .25 * game_state.status.cooldown,  # from 0 to 4
            .04 * sum(map(  # depth 1 starts with 4, depth 16 starts with 28
                lambda demon: self.demon_weights[demon.skill],
                game_state.terrain.demons.values()
            )),
            # if no obstacle, path at the beginning is 9 tiles long
            .11 * path_length,
            int(game_state.terrain.altar_prayable),
        ]
        return numpy.array(features)

    def _evaluate(self, features):
        return features.dot(self.weights)

    def evaluate(self, game_state):
        """Extract the features and evaluate a game state.

        Parameters
        ----------
        game_state : hoplite.game.state.GameState
            State to evaluate.

        Returns
        -------
        float
            Evaluation of the game state.

        """
        return self._evaluate(self.extract(game_state))

    def pick_move(self, game_state):
        """Pick the best move for the player to perform.

        Parameters
        ----------
        game_state : hoplite.game.state.GameState
            Current game state.

        Returns
        -------
        hoplite.game.moves.PlayerMove
            Best legal move to perform according the the model.

        """
        outcomes = dict()
        for move in game_state.possible_moves():
            LOGGER.debug("Checking move: %s", move)
            next_state = move.apply(game_state)
            evaluation = self.evaluate(next_state)
            outcomes[move] = evaluation
            LOGGER.debug("Evaluation of %s: %f", move, evaluation)
        best_move = max(outcomes.items(), key=lambda x: x[1])[0]
        LOGGER.info("Best move found: %s", best_move)
        return best_move

    def pick_prayer(self, altar_state):
        """Pick the best prayer to select from an altar.

        Parameters
        ----------
        altar_state : hoplite.game.state.AltarState
            State of the altar to choose from.

        Returns
        -------
        hoplite.game.status.Prayer
            Prayer choosed from the altar.

        """
        return max(
            altar_state.prayers,
            key=lambda prayer: self.prayer_weights.get(prayer, 0)
        )
