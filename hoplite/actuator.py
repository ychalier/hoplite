"""Interface between the internal game representation and MonkeyRunner.
"""
import hoplite.game.moves


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

    """

    BUTTON_BASH = 180, 1820
    BUTTON_LEAP = 540, 1820
    BUTTON_THROW = 900, 1820

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

    def bash(self, target):
        """Perform a bash move.

        Parameters
        ----------
        target : hoplite.utils.HexagonalCoordinates
            Tile to bash.

        """
        self.button_move(target, Actuator.BUTTON_BASH)

    def throw(self, target):
        """Perform a throw move.

        Parameters
        ----------
        target : hoplite.utils.HexagonalCoordinates
            Tile to throw the spear to.

        """
        self.button_move(target, Actuator.BUTTON_THROW)

    def make_move(self, player_move):
        """Translate a `hoplite.game.moves.PlayerMove` into a sequence of actions
        for the `hoplite.monkey_runner.MonkeyRunnerInterface`.

        Parameters
        ----------
        player_move : hoplite.game.moves.PlayerMove
            Move to perform.

        """
        if isinstance(player_move, hoplite.game.moves.WalkMove):
            self.walk(player_move.target)
        if isinstance(player_move, hoplite.game.moves.LeapMove):
            self.leap(player_move.target)
        if isinstance(player_move, hoplite.game.moves.BashMove):
            self.bash(player_move.target)
        if isinstance(player_move, hoplite.game.moves.ThrowMove):
            self.throw(player_move.target)
