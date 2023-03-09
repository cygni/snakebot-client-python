from dataclasses import dataclass
from enum import Enum
from typing import Literal


@dataclass
class SnakeInfo:
    name: str
    points: int
    positions: list[int]
    tailProtectedForGameTicks: int
    id: str


@dataclass
class RawMap:
    width: int
    height: int
    worldTick: int
    snakeInfos: list[SnakeInfo]
    foodPositions: list[int]
    obstaclePositions: list[int]


class TileType(Enum):
    Empty = "Empty"
    Food = "Food"
    Obstacle = "Obstacle"
    Snake = "Snake"


class GameMode(Enum):
    Training = "TRAINING"
    Tournament = "TOURNAMENT"
    Arena = "ARENA"


class Direction(Enum):
    Up = "UP"
    Down = "DOWN"
    Left = "LEFT"
    Right = "RIGHT"


class RelativeDirection(Enum):
    Forward = "FORWARD"
    Left = "LEFT"
    Right = "RIGHT"


@dataclass
class GameSettings:
    maxNoofPlayers: int
    startSnakeLength: int
    timeInMsPerTick: int
    obstaclesEnabled: bool
    foodEnabled: bool
    headToTailConsumes: bool
    tailConsumeGrows: bool
    addFoodLikelihood: int
    removeFoodLikelihood: int
    spontaneousGrowthEveryNWorldTick: int
    trainingGame: bool
    pointsPerLength: int
    pointsPerFood: int
    pointsPerCausedDeath: int
    pointsPerNibble: int
    noofRoundsTailProtectedAfterNibble: int
    startFood: int
    startObstacles: int
