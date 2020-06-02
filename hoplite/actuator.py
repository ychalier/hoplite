"""Interface between the internal game representation and MonkeyRunner.
"""
import logging
import hoplite.game.moves
import hoplite.game.state


LOGGER = logging.getLogger(__name__)


def hexagonal_to_pixels(pos):
    """Compute the pixel center of an hexagonal tile on screen.

    Parameters
    ----------
    pos : hoplite.utils.HexagonalCoordinates
        Logical position.

    Returns
    -------
    tuple[int, int]
        Position (in pixels) of the center of the tile on the screen.

    """
    column, row = pos.doubled()
    return (
        int(540 + 104 * column),
        int(903 - 112 * row)
    )


class Actuator:
    """Translate a `hoplite.game.moves.PlayerMove` into a sequence of actions
    for the `hoplite.monkey_runner.MonkeyRunnerInterface`.

    Parameters
    ----------
    monkey_runner_interface : hoplite.monkey_runner.MonkeyRunnerInterface.
        MonkeyRunner client.

    Attributes
    ----------
    monkey : hoplite.monkey_runner.MonkeyRunnerInterface
        MonkeyRunner client
    BUTTON_BASH : tuple[int, int]
        Screen position of the bash button.
    BUTTON_LEAP : tuple[int, int]
        Screen position of the leap button.
    BUTTON_THROW : tuple[int, int]
        Screen position of the throw button.
    VICTORY_OK : tuple[int, int]
        Location of the ok button on the victory interface.
    FLEECE_PICK_UP : tuple[int, int]
        Location of the pickup button on the fleece interface.
    EMBARK_EMBARK : tuple[int, int]
        Location of the embark button on the embark interface.
    DEATH_OK : tuple[int, int]
        Location of the ok button on the embark interface.

    """

    BUTTON_BASH = 180, 1820
    BUTTON_LEAP = 540, 1820
    BUTTON_THROW = 900, 1820
    VICTORY_OK = 540, 1673
    FLEECE_PICK_UP = 540, 1222
    EMBARK_EMBARK = 540, 710
    DEATH_OK = 540, 1616

    def __init__(self, monkey_runner_interface):
        self.monkey = monkey_runner_interface

    def walk(self, target):
        """Perform a simple walking move.

        Parameters
        ----------
        target : hoplite.utils.HexagonalCoordinates
            Tile to walk to.

        """
        self.monkey.touch(*hexagonal_to_pixels(target))

    def button_move(self, target, button):
        """First touch a button, then touch another tile.

        Parameters
        ----------
        target : hoplite.utils.HexagonalCoordinates
            Tile touch touch.
        button : tuple[int, int]
            Screen position of the button to touch.

        """
        self.monkey.touch(*button)
        self.monkey.touch(*hexagonal_to_pixels(target))

    def leap(self, target):
        """Perform a leap move.

        Parameters
        ----------
        target : hoplite.utils.HexagonalCoordinates
            Tile to leap to.

        """
        self.button_move(target, Actuator.BUTTON_LEAP)

    def bash(self, target, spinning):
        """Perform a bash move.

        Parameters
        ----------
        target : hoplite.utils.HexagonalCoordinates
            Tile to bash.
        spinning : bool
            If `True`, then the player is bashing while having unlocked the
            "Spinning Bash" prayer. If so, there is no tile to click on, the
            button press is enough to trigger the move.

        """
        if spinning:
            self.monkey.touch(*Actuator.BUTTON_BASH)
        else:
            self.button_move(target, Actuator.BUTTON_BASH)

    def throw(self, target):
        """Perform a throw move.

        Parameters
        ----------
        target : hoplite.utils.HexagonalCoordinates
            Tile to throw the spear to.

        """
        self.button_move(target, Actuator.BUTTON_THROW)

    def make_move(self, player_move, spinning=False):
        """Translate a `hoplite.game.moves.PlayerMove` into a sequence of actions
        for the `hoplite.monkey_runner.MonkeyRunnerInterface`.

        Parameters
        ----------
        player_move : hoplite.game.moves.PlayerMove
            Move to perform.
        spinning : bool
            See `hoplite.actuator.Actuator.bash` for details.

        """
        if isinstance(player_move, hoplite.game.moves.WalkMove):
            self.walk(player_move.target)
        elif isinstance(player_move, hoplite.game.moves.LeapMove):
            self.leap(player_move.target)
        elif isinstance(player_move, hoplite.game.moves.BashMove):
            self.bash(player_move.target, spinning)
        elif isinstance(player_move, hoplite.game.moves.ThrowMove):
            self.throw(player_move.target)
        elif isinstance(player_move, hoplite.game.moves.AltarMove):
            self.monkey.touch(*hexagonal_to_pixels(player_move.target))
        elif isinstance(player_move, hoplite.game.moves.IdleMove):
            self.monkey.touch(*hexagonal_to_pixels(player_move.target))

    def close_interface(self, interface):
        """Take the required action to close an interface, meaning touching
        a button on scree.

        Parameters
        ----------
        interface : hoplite.game.state.Interface
            Interface to close (should be currently displayed on screen).

        """
        LOGGER.debug("Closing interface %s", interface)
        if interface == hoplite.game.state.Interface.EMBARK:
            LOGGER.info("Embarking!")
            self.monkey.touch(*self.EMBARK_EMBARK)
        elif interface == hoplite.game.state.Interface.FLEECE:
            self.monkey.touch(*self.FLEECE_PICK_UP)
        elif interface == hoplite.game.state.Interface.DEATH:
            self.monkey.touch(*self.DEATH_OK)
        elif interface == hoplite.game.state.Interface.VICTORY:
            self.monkey.touch(*self.VICTORY_OK)

    def choose_prayer(self, altar, prayer):
        """Click on a prayer at the altar.

        Parameters
        ----------
        altar : hoplite.game.state.AltarState
            State of the currently displayed altar.
        prayer : hoplite.game.status.Prayer
            Prayer that should be clicked on.

        """
        observed_height = altar.prayers[prayer]
        self.monkey.touch(540, observed_height + 50)
