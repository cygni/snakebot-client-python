import argparse
import importlib.util
import logging
import os
import sys
import textwrap

import colorlog
import twisted
from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.internet import reactor, ssl

from client.client import SnakeImplementation, get_snakebot_protocol

FILE_DIR = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger("client")
log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "fatal": logging.FATAL,
}
log_names = list(log_levels)


def _set_up_logging(args):
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        fmt=(
            "%(log_color)s[%(asctime)s %(levelname)8s] --"
            " %(message)s (%(filename)s:%(lineno)s)"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    log.addHandler(handler)
    log.setLevel(log_levels[args.log_level])


def get_snake(snake_path: str) -> SnakeImplementation:
    """
    Magically load a snake from a file path
    """

    if snake_path is None:
        return None

    snake_path = os.path.join(FILE_DIR, snake_path)
    module_name = os.path.basename(snake_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, snake_path)
    snake_module = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[spec.name] = snake_module  # type: ignore
    spec.loader.exec_module(snake_module)  # type: ignore

    snake = snake_module.get_snake()

    return snake


def main(args):
    _set_up_logging(args)

    if args.venue.upper() not in ("TRAINING", "TOURNAMENT"):
        venue = args.venue.upper()
        venue = "arena/" + args.venue
    else:
        venue = args.venue.lower()

    factory = WebSocketClientFactory("wss://%s:%s/%s" % (args.host, args.port, venue))
    factory.protocol = get_snakebot_protocol(
        get_snake(args.snake),
        args.spoiler,
    )

    if factory.isSecure:
        contextFactory = ssl.ClientContextFactory()
    else:
        contextFactory = None

    connectWS(factory, contextFactory)
    reactor.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """
        Connect to a snake server and play a game

        Example:
            python snake-cli.py --host http://localhost:8080 --venue training --name Slither --snake ./snakepit/slither.py
        Or:
            python snake-cli.py -h http://localhost:8080 -v training -n Slither -s ./snakepit/slither.py
        """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--host", help="Hostname of the server", default="snake.cygni.se"
    )
    parser.add_argument("-p", "--port", help="Port of the server", default=443)
    parser.add_argument(
        "-v",
        "--venue",
        help="Venue name. Possible values: training, arenaID, tournament",
        default="training",
    )
    parser.add_argument("-n", "--name", help="Name of the snake", default="Slither")
    parser.add_argument(
        "-s", "--snake", help="Path to the snake file", default="./snakepit/snake.py"
    )
    parser.add_argument(
        "-sp", "--spoiler", help="Show the results", action="store_true"
    )
    parser.add_argument(
        "-l",
        "--log-level",
        default=log_names[0],
        choices=log_names,
        help="The log level for the client",
    )
    args = parser.parse_args()

    main(args)
