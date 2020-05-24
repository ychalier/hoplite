"""Interface between the `hoplite.vision.observer.Observer`,
the `hoplite.brain.Brain` the `hoplite.actuator.Actuator`. Plays the game.
"""

import time
import logging
import hoplite.game.state


LOGGER = logging.getLogger(__name__)


class Controller:
    """Game controller.

    Parameters
    ----------
    observer : hoplite.vision.observer.Observer
        Eyes of the controller.
    actuator : hoplite.actuator.Actuator
        Fingers of the controller.
    brain : hoplite.brain.Brain
        Mind of the controller.

    Attributes
    ----------
    stop : bool
        Whether the controller main loop should be stopped.
    memory : hoplite.game.state.GameState
        Last known state of the game.
    observer
    actuator
    brain

    """

    def __init__(self, observer, actuator, brain):
        self.observer = observer
        self.actuator = actuator
        self.brain = brain
        self.memory = None
        self.stop = False

    def step(self):
        """One step of the game: recognition, decision and action.
        """
        interface = self.observer.fetch_screenshot()
        LOGGER.debug("Interface: %s", interface)
        if self.memory:
            print(self.memory.status.prayers)
        if interface == hoplite.game.state.Interface.PLAYING:
            game = self.observer.parse_game()
            if self.memory is None:
                self.memory = game
            else:
                self.memory.update(game)
            move = self.brain.pick_move(self.memory)
            self.actuator.make_move(move)
        elif interface == hoplite.game.state.Interface.EMBARK:
            self.actuator.close_interface(interface)
        elif interface == hoplite.game.state.Interface.DEATH:
            self.stop = True
            LOGGER.info("The player is dead.")
        elif interface == hoplite.game.state.Interface.VICTORY:
            self.stop = True
            LOGGER.info("The player has won!")
        elif interface == hoplite.game.state.Interface.ALTAR:
            altar = self.observer.parse_altar()
            LOGGER.info("Available prayers: %s", altar)
            prayer = self.brain.pick_prayer(altar)
            self.memory.status.prayers.append(prayer)
            LOGGER.info("Picked prayer %s", prayer)
            self.actuator.choose_prayer(altar, prayer)
        elif interface == hoplite.game.state.Interface.FLEECE:
            self.actuator.close_interface(interface)
        time.sleep(1)

    def run(self):
        """Main loop. Stops when the `stop` attribute is `False`.
        """
        while not self.stop:
            try:
                self.step()
            except KeyboardInterrupt:
                LOGGER.warning("Interrupting the controller.")
                self.stop = True
