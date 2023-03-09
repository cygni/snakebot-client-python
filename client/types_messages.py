from dataclasses import dataclass

from .types import GameMode, GameSettings, RawMap


@dataclass
class Message:
    type: str
    receivingPlayerId: str
    timestamp: int


@dataclass
class HeartBeatResponseMessage(Message):
    pass


@dataclass
class PlayerRegisteredMessage(Message):
    gameId: str
    name: str
    gameSettings: GameSettings
    gameMode: GameMode


@dataclass
class GameLinkEventMessage(Message):
    url: str


@dataclass
class GameStartingEventMessage(Message):
    gameId: str
    noofPlayers: int
    width: int
    height: int
    gameSettings: GameSettings


@dataclass
class MapUpdateEventMessage(Message):
    gameTick: int
    gameId: str
    map: RawMap


@dataclass
class SnakeDeadEventMessage(Message):
    deathReason: str
    playerId: str
    x: int
    y: int
    gameId: str
    gameTick: int


@dataclass
class PlayerRank:
    playerName: str
    playerId: str
    rank: int
    points: int
    alive: bool


@dataclass
class GameResultEventMessage(Message):
    gameId: str
    playerRanks: list[PlayerRank]


@dataclass
class GameEndedEventMessage(Message):
    playerWinnerId: str
    playerWinnerName: str
    gameId: str
    gameTick: int
    map: RawMap


@dataclass
class InvalidPlayerNameMessage(Message):
    reasonCode: str


@dataclass
class GameResult:
    name: str
    playerId: str
    points: int


@dataclass
class TournamentEndedMessage(Message):
    playerWinnerId: str
    gameId: str
    gameResult: GameResult
    tournamentName: str
    tournamentId: str


@dataclass
class NoActiveTournamentMessage(Message):
    pass


@dataclass
class ArenaIsFullMessage(Message):
    playersConnected: int


@dataclass
class InvalidMessage(Message):
    errorMessage: str
    receivedMessage: str
