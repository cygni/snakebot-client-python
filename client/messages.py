import platform
import sys
from enum import Enum


class MessageType(Enum):
    # Exceptions
    InvalidMessage = "se.cygni.snake.api.exception.InvalidMessage"
    InvalidPlayerName = "se.cygni.snake.api.exception.InvalidPlayerName"
    NoActiveTournament = "se.cygni.snake.api.exception.NoActiveTournament"
    InvalidArenaName = "se.cygni.snake.api.exception.InvalidArenaName"
    ArenaIsFull = "se.cygni.snake.api.exception.ArenaIsFull"

    # Responses
    HeartbeatResponse = "se.cygni.snake.api.response.HeartBeatResponse"
    PlayerRegistered = "se.cygni.snake.api.response.PlayerRegistered"

    # Events
    GameLink = "se.cygni.snake.api.event.GameLinkEvent"
    GameStarting = "se.cygni.snake.api.event.GameStartingEvent"
    MapUpdate = "se.cygni.snake.api.event.MapUpdateEvent"
    SnakeDead = "se.cygni.snake.api.event.SnakeDeadEvent"
    GameResult = "se.cygni.snake.api.event.GameResultEvent"
    GameEnded = "se.cygni.snake.api.event.GameEndedEvent"
    TournamentEnded = "se.cygni.snake.api.event.TournamentEndedEvent"

    # Requests
    ClientInfo = "se.cygni.snake.api.request.ClientInfo"
    StartGame = "se.cygni.snake.api.request.StartGame"
    RegisterPlayer = "se.cygni.snake.api.request.RegisterPlayer"
    RegisterMove = "se.cygni.snake.api.request.RegisterMove"
    HeartbeatRequest = "se.cygni.snake.api.request.HeartBeatRequest"


def create_client_info_message():
    python_version_string = ".".join(
        [
            str(sys.version_info.major),
            str(sys.version_info.minor),
            str(sys.version_info.micro),
        ]
    )

    platform_name = platform.system()
    os_name = "Maybe Linux"
    os_version = "0.0.0"

    if platform_name == "linux" or platform_name == "linux2":
        os_name, os_version, _ = platform.linux_distribution()
    elif platform_name == "darwin" or platform_name == "Darwin":
        os_name = "macOS"
        os_version, _, _ = platform.mac_ver()
    elif platform_name == "win32":
        os_name = "Windows"
        os_version, _, _ = platform.win32_ver()

    return {
        "type": MessageType.ClientInfo.value,
        "language": "Python",
        "languageVersion": python_version_string,
        "clientVersion": 2.0,
        "operatingSystem": os_name,
        "operatingSystemVersion": os_version,
    }


def create_heartbeat_request_message(receiving_player_id):
    return {
        "type": MessageType.HeartbeatRequest.value,
        "receivingPlayerId": receiving_player_id,
    }


def create_register_move_message(direction, receiving_player_id, game_id, game_tick):
    return {
        "type": MessageType.RegisterMove.value,
        "direction": direction,
        "receivingPlayerId": receiving_player_id,
        "gameId": game_id,
        "gameTick": game_tick,
    }


def create_register_player_message(player_name, game_settings):
    return {
        "type": MessageType.RegisterPlayer.value,
        "playerName": player_name,
        "gameSettings": game_settings,
    }


def create_start_game_message():
    return {
        "type": MessageType.StartGame.value,
    }
