import math

from .types import (
    Direction,
    GameSettings,
    RawMap,
    RelativeDirection,
    SnakeInfo,
    TileType,
)


def get_direction_delta(direction: Direction) -> tuple[int, int]:
    if direction == Direction.Up:
        return 0, -1
    elif direction == Direction.Down:
        return 0, 1
    elif direction == Direction.Left:
        return -1, 0
    elif direction == Direction.Right:
        return 1, 0
    else:
        raise ValueError(f"Unknown direction: {direction}")


class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def from_position(position: int, map_height: int) -> "Coordinate":
        x = position % map_height
        y = (position - x) / map_height
        return Coordinate(x, y)

    def is_within_square(
        self, northwest: "Coordinate", southeast: "Coordinate"
    ) -> bool:
        return (
            self.x >= northwest.x
            and self.x <= southeast.x
            and self.y >= northwest.y
            and self.y <= southeast.y
        )

    def is_out_of_bounds(self, map_width: int, map_height: int) -> bool:
        return self.x < 0 or self.y < 0 or self.x >= map_width or self.y >= map_height

    def euclidian_distance_to(self, other_coordinate: "Coordinate") -> float:
        return math.sqrt(
            math.pow(other_coordinate.x - self.x, 2)
            + math.pow(other_coordinate.y - self.y, 2)
        )

    def manhattan_distance_to(self, other_coordinate: "Coordinate") -> int:
        return abs(other_coordinate.x - self.x) + abs(other_coordinate.y - self.y)

    def delta_to(self, other_coordinate: "Coordinate") -> tuple[int, int]:
        delta_x = other_coordinate.x - self.x
        delta_y = other_coordinate.y - self.y
        return delta_x, delta_y

    def to_position(self, map_width: int, map_height: int) -> int:
        if self.is_out_of_bounds(map_width, map_height):
            raise ValueError(
                "The coordinate must be within the bounds in order to convert to position"
            )
        return self.x + self.y * map_width

    def negated(self) -> "Coordinate":
        return Coordinate(-self.x, -self.y)

    def translate_by_delta(self, delta_x: int, delta_y: int) -> "Coordinate":
        return Coordinate(self.x + delta_x, self.y + delta_y)

    def translate_by_direction(self, direction: Direction) -> "Coordinate":
        delta_x, delta_y = get_direction_delta(direction)
        return self.translate_by_delta(delta_x, delta_y)

    def direction_to(self, other_coordinate: "Coordinate") -> Direction:
        delta_x, delta_y = self.delta_to(other_coordinate)
        if delta_x == 0 and delta_y == -1:
            return Direction.Up
        elif delta_x == 0 and delta_y == 1:
            return Direction.Down
        elif delta_x == -1 and delta_y == 0:
            return Direction.Left
        elif delta_x == 1 and delta_y == 0:
            return Direction.Right
        else:
            raise ValueError(
                f"Coordinate is too far away! Difference is ({delta_x}, {delta_y})"
            )


class GameMap:
    def __init__(
        self, map: RawMap, player_id: str, game_settings: GameSettings, game_tick: int
    ):
        snakes = {}
        tiles = {}

        for food_position in map.foodPositions:
            tiles[food_position] = TileType.Food

        for obstacle_position in map.obstaclePositions:
            tiles[obstacle_position] = TileType.Obstacle

        for snake_info in map.snakeInfos:
            snake = Snake.from_snake_info(snake_info, map.width, self)
            snakes[snake_info.id] = snake
            for snake_position in snake_info.positions:
                tiles[snake_position] = TileType.Snake

        self.player_id = player_id
        self.width = map.width
        self.height = map.height
        self.snakes = snakes
        self.tiles = tiles
        self.game_settings = game_settings
        self.game_tick = game_tick

    @property
    def player_snake(self) -> "Snake":
        return self.snakes[self.player_id]

    def get_tile_type(self, coordinate: Coordinate) -> TileType:
        width, height = self.width, self.height

        if coordinate.is_out_of_bounds(width, height):
            return TileType.Obstacle

        position = coordinate.to_position(width, height)
        tile_type = self.tiles.get(position)

        if tile_type is None:
            return TileType.Empty

        return tile_type

    def is_tile_free(self, coordinate: Coordinate) -> bool:
        return self.get_tile_type(coordinate) in (TileType.Empty, TileType.Food)


class Snake:
    def __init__(
        self,
        id: str,
        name: str,
        direction: Direction,
        coordinates: list[Coordinate],
        map: GameMap,
    ):
        self.id = id
        self.name = name
        self.direction = direction
        self.coordinates = coordinates
        self.map = map

    @classmethod
    def from_snake_info(cls, snake_info: SnakeInfo, map_width: int, map: GameMap):
        id = snake_info.id
        name = snake_info.name
        positions = snake_info.positions
        coordinates = [
            Coordinate.from_position(position, map_width) for position in positions
        ]
        # Calculate the direction of the snake
        direction = Direction.Up
        if len(coordinates) > 1:
            delta_x, delta_y = coordinates[1].delta_to(coordinates[0])
            if delta_x == 1:
                direction = Direction.Right
            elif delta_x == -1:
                direction = Direction.Left
            elif delta_y == 1:
                direction = Direction.Down
            elif delta_y == -1:
                direction = Direction.Up

        return cls(id, name, direction, coordinates, map)

    def can_move_in_direction(self, direction: Direction) -> bool:
        snake_head = self.coordinates[0]
        next_coord = snake_head.translate_by_direction(direction)
        return self.map.is_tile_free(next_coord)

    def relative_to_absolute(self, relative_direction: RelativeDirection) -> Direction:
        if relative_direction == RelativeDirection.Forward:
            return self.direction
        elif relative_direction == RelativeDirection.Left:
            if self.direction == Direction.Up:
                return Direction.Left
            elif self.direction == Direction.Down:
                return Direction.Right
            elif self.direction == Direction.Left:
                return Direction.Down
            elif self.direction == Direction.Right:
                return Direction.Up
        elif relative_direction == RelativeDirection.Right:
            if self.direction == Direction.Up:
                return Direction.Right
            elif self.direction == Direction.Down:
                return Direction.Left
            elif self.direction == Direction.Left:
                return Direction.Up
            elif self.direction == Direction.Right:
                return Direction.Down

        raise Exception(f"Unknown direction: {self.direction}")

    @property
    def head_coordinate(self) -> Coordinate:
        return self.coordinates[0]

    @property
    def tail_coordinate(self) -> Coordinate:
        return self.coordinates[-1]

    @property
    def length(self) -> int:
        return len(self.coordinates)
