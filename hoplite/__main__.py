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
import hoplite.vision.observer
import hoplite.controller
import hoplite.monkey_runner
import hoplite.actuator
import hoplite.brain


def play(monkey_runner, save_screenshots, prayers):
    """Play with the monkey runner interface.
    """
    mr_if = hoplite.monkey_runner.MonkeyRunnerInterface(monkey_runner)
    observer = hoplite.vision.observer.Observer(mr_if, save_screenshots=save_screenshots)
    actuator = hoplite.actuator.Actuator(mr_if)
    brain = hoplite.brain.Brain()
    starting_prayers = list()
    for prayer in prayers.strip().split(","):
        if prayer == "":
            continue
        starting_prayers.append(hoplite.game.status.Prayer(int(prayer)))
    controller = hoplite.controller.Controller(observer, actuator, brain, starting_prayers)
    mr_if.open()
    try:
        controller.run()
    except KeyboardInterrupt:
        logging.warning("Interrupting with keyboard")
    finally:
        try:
            mr_if.close()
        except KeyboardInterrupt:
            pass


def parse(path, save_parts, show_ranges, prayers, render):
    """Parse a screenshot.
    """
    parser = hoplite.vision.observer.ScreenParser(save_parts=save_parts)
    brain = hoplite.brain.Brain()
    game = parser.observe_game(parser.read_stream(path))
    for prayer in prayers.strip().split(","):
        if prayer == "":
            continue
        game.status.add_prayer(hoplite.game.status.Prayer(int(prayer)))
    print(repr(game))
    logging.info("Evaluation: %s", brain.evaluate(game))
    brain.pick_move(game)
    if render:
        game.terrain.render(show_ranges=show_ranges)


def move(path, move_name, target, prayers, render):
    """Observe a screenshot and make a move.
    """
    parser = hoplite.vision.observer.ScreenParser()
    prev_state = parser.observe_game(parser.read_stream(path))
    for prayer in prayers.strip().split(","):
        if prayer == "":
            continue
        prev_state.status.add_prayer(hoplite.game.status.Prayer(int(prayer)))
    prev_state.terrain.render()
    move_class = {
        "walk": hoplite.game.moves.WalkMove,
        "leap": hoplite.game.moves.LeapMove,
        "bash": hoplite.game.moves.BashMove,
        "throw": hoplite.game.moves.ThrowMove
    }[move_name]
    player_move = move_class(hoplite.utils.HexagonalCoordinates(*target))
    next_state = player_move.apply(prev_state)
    print(repr(next_state))
    if render:
        next_state.terrain.render()


def main():
    """Argument parsing and action taking.
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
    parse_parser = subparsers.add_parser("parse")
    parse_parser.add_argument(
        "path",
        type=str,
        help="path to PNG screenshot file"
    )
    parse_parser.add_argument(
        "--save-parts",
        action="store_true",
        help="save extracted parts to disk"
    )
    parse_parser.add_argument(
        "--show-ranges",
        action="store_true",
        help="show ranges",
    )
    parse_parser.add_argument(
        "--prayers",
        type=str,
        help="comma separated prayer index",
        default="",
    )
    parse_parser.add_argument(
        "-r", "--render",
        action="store_true",
        help="render the terrain in a Pygame window",
    )
    move_parser = subparsers.add_parser("move")
    move_parser.add_argument(
        "path",
        type=str,
        help="path to PNG screenshot file"
    )
    move_parser.add_argument(
        "move",
        choices=["walk", "leap", "bash", "throw"],
        help="player move to perform"
    )
    move_parser.add_argument(
        "x",
        type=int,
        help="move target x"
    )
    move_parser.add_argument(
        "y",
        type=int,
        help="move target y"
    )
    move_parser.add_argument(
        "--prayers",
        type=str,
        help="comma separated prayer index",
        default="",
    )
    move_parser.add_argument(
        "-r", "--render",
        action="store_true",
        help="render the terrain in a Pygame window",
    )
    play_parser = subparsers.add_parser("play")
    play_parser.add_argument(
        "--save-screenshots",
        action="store_true",
        help="store screenshots as they are taken"
    )
    play_parser.add_argument(
        "--prayers",
        type=str,
        help="comma separated prayer index",
        default="",
    )
    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    elif args.silent:
        log_level = logging.CRITICAL
    logging.basicConfig(level=log_level)
    if args.action == "parse":
        parse(args.path, args.save_parts, args.show_ranges, args.prayers, args.render)
    elif args.action == "move":
        move(args.path, args.move, (args.x, args.y), args.prayers, args.render)
    elif args.action == "play":
        play(args.monkey_runner, args.save_screenshots, args.prayers)


main()
