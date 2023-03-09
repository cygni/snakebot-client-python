import logging

from client.client import SnakeImplementation
from client.types import Direction

log = logging.getLogger("client.snake")


class Snake(SnakeImplementation):
    def __init__(self):
        self.name = "snake.py"
        self.snake_id = None

    def get_next_move(self, game_map):
        return Direction.Down


def get_snake():
    return Snake()
