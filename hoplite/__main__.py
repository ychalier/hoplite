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


def parse(args):
    """Parse a game state to perform some analysis.
    """
    if os.path.isfile(args.input):
        parser = hoplite.vision.observer.ScreenParser(save_parts=args.save_parts)
        game = parser.observe_game(parser.read_stream(args.input))
    else:
        game = hoplite.game.state.GameState.from_string(args.input)
    for prayer in args.prayers.strip().split(","):
        if prayer != "":
            game.status.add_prayer(hoplite.game.status.Prayer(int(prayer)))
    if "move_type" in args:
        move_class = {
            "walk": hoplite.game.moves.WalkMove,
            "leap": hoplite.game.moves.LeapMove,
            "bash": hoplite.game.moves.BashMove,
            "throw": hoplite.game.moves.ThrowMove
        }[args.move_type]
        player_move = move_class(hoplite.utils.HexagonalCoordinates(args.x, args.y))
        game = player_move.apply(game)
    print(repr(game))
    if args.evaluate:
        brain = hoplite.brain.Brain()
        print("evaluation:\t%f" % brain.evaluate(game))
        print("best move:\t%s" % brain.pick_move(game))
    if args.render:
        game.terrain.render(show_ranges=args.show_ranges)


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
    parse_parser = subparsers.add_parser("parse")
    parse_parser.add_argument(
        "-i", "--input",
        type=str,
        help="game state notation or path to a screenshot"
    )
    parse_subparsers = parse_parser.add_subparsers()
    parse_parser.add_argument(
        "-p", "--prayers",
        type=str,
        help="comma separated prayer indices",
        default=""
    )
    parse_parser.add_argument(
        "-r", "--render",
        action="store_true",
        help="render the terrain using a PyGame window"
    )
    parse_parser.add_argument(
        "-sp", "--save-parts",
        action="store_true",
        help="save parts extracted during the screenshot observation to the disk"
    )
    parse_parser.add_argument(
        "-sr", "--show-ranges",
        action="store_true",
        help="when rendering, render demon ranges"
    )
    parse_parser.add_argument(
        "-ev", "--evaluate",
        action="store_true",
        help="evaluate the input game state"
    )
    move_parser = parse_subparsers.add_parser("move")
    move_parser.add_argument(
        "move_type",
        type=str,
        choices=["walk", "leap", "bash", "throw"],
        help="move to perform within the input state"
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
    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    elif args.silent:
        log_level = logging.CRITICAL
    logging.basicConfig(level=log_level)
    if args.action == "play":
        play(args.monkey_runner, args.save_screenshots, args.prayers)
    elif args.action == "parse":
        parse(args)


main()
