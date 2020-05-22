# pylint: disable=C0413
"""
Hoplite game AI
"""

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import argparse
import logging
import hoplite
import hoplite.utils
import hoplite.game.terrain
import hoplite.game.moves
import hoplite.game.state
import hoplite.observer
import hoplite.controller
import hoplite.monkey_runner
import hoplite.actuator


def dev():
    """
    Temporary function to test some features
    """
    state = hoplite.game.state.GameState()
    for pos in hoplite.utils.SURFACE_COORDINATES:
        state.terrain.surface[pos] = hoplite.game.terrain.Tile.GROUND
    state.terrain.render()


def play(monkey_runner):
    """
    Play with the monkey runner interface.
    """
    observer = hoplite.observer.Observer()
    observer.build()
    controller = hoplite.controller.Controller()
    mr_if = hoplite.monkey_runner.MonkeyRunnerInterface(monkey_runner)
    actuator = hoplite.actuator.Actuator(mr_if)
    mr_if.open()
    while True:
        state = observer.observe_stream(mr_if.snapshot(as_stream=True))
        move = controller.pick_move(state)
        actuator.make_move(move)
        observer.wait(mr_if, .05)  # TODO: allow user input & improve
    mr_if.close()


def observe(path, save_parts, show_ranges):
    """
    Observe a screenshot.
    """
    observer = hoplite.observer.Observer(save_parts)
    observer.build()
    controller = hoplite.controller.Controller()
    state = observer.observe_stream(path)
    print(state)
    print("Evaluation:", controller.evaluate(state))
    print("Best move:", controller.pick_move(state))
    state.terrain.render(show_ranges=show_ranges)



def observe_and_move(path, move, target):
    """
    Observe a screenshot and make a move.
    """
    observer = hoplite.observer.Observer()
    observer.build()
    prev_state = observer.observe_stream(path)
    print(prev_state)
    prev_state.terrain.render()
    move_class = {
        "walk": hoplite.game.moves.WalkMove,
        "leap": hoplite.game.moves.LeapMove,
        "bash": hoplite.game.moves.BashMove,
        "throw": hoplite.game.moves.ThrowMove
    }[move]
    move = move_class(hoplite.utils.HexagonalCoordinates(*target))
    next_state = move.apply(prev_state)
    print(next_state)
    next_state.terrain.render()


def main():
    """
    Argument parsing and action taking.
    """
    description = "\n".join((
        "Hoplite AI version %s." % hoplite.__version__,
        "Check repository at https://github.com/ychalier/hoplite"
    ))
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-mkr", "--monkey-runner",
        type=str,
        help="path to MonkeyRunner script",
        default="C:\\Users\\yohan\\AppData\\Local\\Android\\Sdk\\tools\\bin\\monkeyrunner.bat"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="see debug messages"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="only see warnings and errors"
    )
    parser.add_argument(
        "-s", "--silent",
        action="store_true",
        help="no logging output"
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    observe_parser = subparsers.add_parser("observe")
    observe_parser.add_argument(
        "path",
        type=str,
        help="path to PNG screenshot file"
    )
    observe_parser.add_argument(
        "--save-parts",
        action="store_true",
        help="save extracted parts to disk"
    )
    observe_parser.add_argument(
        "--show-ranges",
        action="store_true",
        help="show ranges",
    )
    observer_and_move_parser = subparsers.add_parser("observe_and_move")
    observer_and_move_parser.add_argument(
        "path",
        type=str,
        help="path to PNG screenshot file"
    )
    observer_and_move_parser.add_argument(
        "move",
        choices=["walk", "leap", "bash", "throw"],
        help="player move to perform"
    )
    observer_and_move_parser.add_argument(
        "x",
        type=int,
        help="move target x"
    )
    observer_and_move_parser.add_argument(
        "y",
        type=int,
        help="move target y"
    )
    subparsers.add_parser("dev")
    subparsers.add_parser("play")
    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    elif args.silent:
        log_level = logging.CRITICAL
    logging.basicConfig(level=log_level)
    if args.action == "observe":
        observe(args.path, args.save_parts, args.show_ranges)
    elif args.action == "observe_and_move":
        observe_and_move(args.path, args.move, (args.x, args.y))
    elif args.action == "dev":
        dev()
    elif args.action == "play":
        play(args.monkey_runner)


main()
