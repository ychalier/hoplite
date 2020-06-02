"""Interface between the `hoplite.vision.observer.Observer`,
the `hoplite.brain.Brain` the `hoplite.actuator.Actuator`. Plays the game.
"""

import os
import time
import logging
import hoplite
import hoplite.game.state


LOGGER = logging.getLogger(__name__)


class Recorder:
    """Game recorder. Records states and screenshots encountered while playing
    the game.

    Parameters
    ----------
    observer : hoplite.vision.observer.Observer
        Reference to an observer to save the screenshots from.

    Attributes
    ----------
    folder : str
        Path to the folder containing all the data about the current recording.
    DIRECTORY : str
        Path to the folder containing all recordings.
    FILENAME : str
        Basename of the file containing the state logs.
    observer

    """

    DIRECTORY = "recordings"
    FILENAME = "game.log"

    def __init__(self, observer):
        self.observer = observer
        if not os.path.isdir(Recorder.DIRECTORY):
            LOGGER.info(
                "Creating recordings directory at '%s'",
                os.path.realpath(Recorder.DIRECTORY)
            )
            os.mkdir(Recorder.DIRECTORY)
        self.folder = None

    def start(self):
        """Create the folder structure for the recording.
        """
        index = len(next(os.walk(Recorder.DIRECTORY))[1]) + 1
        self.folder = str(index).rjust(3, "0")
        os.mkdir(os.path.join(Recorder.DIRECTORY, self.folder))
        LOGGER.info("Initializing recording at %s", os.path.realpath(self.folder))
        open(os.path.join(Recorder.DIRECTORY, self.folder, Recorder.FILENAME), "w").close()

    def _record(self, turn, line):
        self.observer.save_screenshot(os.path.join(
            Recorder.DIRECTORY,
            self.folder,
            str(turn).rjust(3, "0") + ".png"
        ))
        with open(os.path.join(Recorder.DIRECTORY, self.folder, Recorder.FILENAME), "a") as file:
            file.write("%s\t%s\n" % (str(turn).rjust(3, "0"), line))

    def record_move(self, turn, game_state, move):
        """Append a move record.

        Parameters
        ----------
        turn : int
            Controller's turn, used to name the screenshot file.
        game_state : hoplite.game.state.GameState
            Current state of the game to the controller's knowledge.
        move : hoplite.game.moves.PlayerMove
            Move that the controller picked to perform in this state.

        """
        self._record(turn, "\t".join(["move", repr(game_state), repr(move)]))

    def record_altar(self, turn, altar_state, prayer):
        """Append an altar prayer selection record.

        Parameters
        ----------
        turn : int
            Controller's turn, used to name the screenshot file.
        altar_state : hoplite.game.state.AltarState
            State of the altar as to the controller's knowledge.
        prayer : hoplite.game.status.Prayer
            Prayer the controller picked for selection.

        """
        self._record(turn, "\t".join(["altar", repr(altar_state), str(prayer.value)]))


class Controller:  # pylint: disable=R0902
    """Game controller.

    Parameters
    ----------
    observer : hoplite.vision.observer.Observer
        Eyes of the controller.
    actuator : hoplite.actuator.Actuator
        Fingers of the controller.
    brain : hoplite.brain.Brain
        Mind of the controller.
    starting_prayers : list[hoplite.game.status.Prayer]
        Prayers to artificially add to the first encountered game status.
    recorder : Recorder
        Game recorder.

    Attributes
    ----------
    stop : bool
        Whether the controller main loop should be stopped.
    memory : hoplite.game.state.GameState
        Last known state of the game.
    turn : int
        Current controller turn; may differ from internal game's turn count,
        as interface here count as full turns.
    observer
    actuator
    brain
    starting_prayers

    """

    def __init__(self, observer, actuator, brain, starting_prayers=None, recorder=None):  # pylint: disable=R0913
        self.observer = observer
        self.actuator = actuator
        self.brain = brain
        self.starting_prayers = starting_prayers
        self.recorder = recorder
        self.stop = False
        self.memory = None
        self.turn = 1

    def step(self):  # pylint: disable=R0912
        """One step of the game: recognition, decision and action.
        """
        interface = self.observer.fetch_screenshot()
        LOGGER.debug("Interface: %s", interface)
        if interface == hoplite.game.state.Interface.PLAYING:
            game = self.observer.parse_game()
            if self.memory is None:
                self.memory = game
                if self.starting_prayers:
                    for prayer in self.starting_prayers:
                        self.memory.status.add_prayer(prayer, False)
            else:
                self.memory.update(game)
            LOGGER.info("Current evaluation: %.2f", self.brain.evaluate(self.memory))
            move = self.brain.pick_move(self.memory)
            self.actuator.make_move(
                move,
                spinning=hoplite.game.status.Prayer.SPINNING_BASH in self.memory.status.prayers
            )
            if self.recorder is not None:
                self.recorder.record_move(self.turn, self.memory, move)
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
            self.memory.status.add_prayer(prayer)
            LOGGER.info("Picked prayer %s", prayer)
            self.actuator.choose_prayer(altar, prayer)
            if self.recorder is not None:
                self.recorder.record_altar(self.turn, altar, prayer)
        elif interface == hoplite.game.state.Interface.FLEECE:
            self.actuator.close_interface(interface)
        elif interface == hoplite.game.state.Interface.STAIRS:
            self.stop = True
            LOGGER.info("Reached the stairs!")
        self.turn += 1
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
