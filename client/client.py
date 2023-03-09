import json
import logging
from typing import Any, get_args

from autobahn.twisted.websocket import WebSocketClientProtocol
from twisted.internet import reactor

from .messages import (
    MessageType,
    create_client_info_message,
    create_heartbeat_request_message,
    create_register_move_message,
    create_register_player_message,
    create_start_game_message,
)
from .types import GameMode, GameSettings
from .types_messages import (
    ArenaIsFullMessage,
    GameEndedEventMessage,
    GameLinkEventMessage,
    GameResultEventMessage,
    GameStartingEventMessage,
    HeartBeatResponseMessage,
    InvalidMessage,
    InvalidPlayerNameMessage,
    MapUpdateEventMessage,
    Message,
    NoActiveTournamentMessage,
    PlayerRegisteredMessage,
    SnakeDeadEventMessage,
    TournamentEndedMessage,
)
from .util import GameMap

HEARTBEAT_INTERVAL = 5000  # ms
SUPPORTED_GAME_MODES = set(get_args(GameMode))

log = logging.getLogger("client")


class SnakeImplementation:
    def __init__(self, get_next_move, on_message=None, training_game_settings=None):
        self.get_next_move = get_next_move
        self.on_message = on_message
        self.training_game_settings = training_game_settings


def get_snakebot_protocol(
    snake: SnakeImplementation,
    spoiler: bool = True,
):
    class SnakebotProtocol(WebSocketClientProtocol):
        def __init__(self):
            self.snake = snake
            self.spoiler = spoiler
            super(WebSocketClientProtocol, self).__init__()
            self.routing_fun = {
                MessageType.PlayerRegistered: self._player_registered,
                MessageType.HeartbeatResponse: self._heartbeat_response,
                MessageType.GameLink: self._game_link,
                MessageType.GameStarting: self._game_starting,
                MessageType.MapUpdate: self._map_update,
                MessageType.SnakeDead: self._snake_dead,
                MessageType.GameResult: self._game_result,
                MessageType.GameEnded: self._game_ended,
                MessageType.InvalidPlayerName: self._invalid_player_name,
                MessageType.TournamentEnded: self._tournament_ended,
                MessageType.NoActiveTournament: self._no_active_tournament,
                MessageType.InvalidArenaName: self._invalid_arena_name,
                MessageType.ArenaIsFull: self._arena_is_full,
                MessageType.InvalidMessage: self._invalid_message,
            }
            self.routing_dataclass = {
                MessageType.PlayerRegistered: PlayerRegisteredMessage,
                MessageType.HeartbeatResponse: HeartBeatResponseMessage,
                MessageType.GameLink: GameLinkEventMessage,
                MessageType.GameStarting: GameStartingEventMessage,
                MessageType.MapUpdate: MapUpdateEventMessage,
                MessageType.SnakeDead: SnakeDeadEventMessage,
                MessageType.GameResult: GameResultEventMessage,
                MessageType.GameEnded: GameEndedEventMessage,
                MessageType.InvalidPlayerName: InvalidPlayerNameMessage,
                MessageType.TournamentEnded: TournamentEndedMessage,
                MessageType.NoActiveTournament: NoActiveTournamentMessage,
                MessageType.InvalidArenaName: InvalidPlayerNameMessage,
                MessageType.ArenaIsFull: ArenaIsFullMessage,
                MessageType.InvalidMessage: InvalidMessage,
            }

            # Is tournament: false by default
            # Sets to true when player registers
            # and game mode is tournament.
            self.is_tournament = False

        def onOpen(self):
            log.info("connection is open")
            self._send(create_client_info_message())
            self._send(create_register_player_message(self.snake.name))

        def onMessage(self, payload, isBinary):
            assert not isBinary
            if isBinary:
                log.error("Received binary message, ignoring...")
                return

            msg = json.loads(payload.decode())
            log.debug("Message received: %s", msg)

            dc = self.routing_dataclass.get(msg["type"], None)

            self._route_message(dc(**msg))

            if self.snake.on_message is not None:
                self.snake.on_message(msg)

        def onClose(self, wasClean, code, reason):
            log.info("Socket is closed!")
            if reason:
                log.error(reason)

            if self.is_tournament and self.heart_beat is not None:
                self.heart_beat.cancel()
            else:
                self._done(None)

        def _done(self, task):
            reactor.stop()

        def _send(self, msg):
            log.debug("Sending message: %s", msg)
            self.sendMessage(json.dumps(msg).encode(), False)

        def _route_message(self, msg):
            fun = self.routing_fun.get(msg["type"], None)
            dc = self.routing_dataclass.get(msg["type"], None)

            if fun:
                fun(dc(**msg))
            else:
                self._unrecognized_message(msg)

        def _player_registered(self, msg: PlayerRegisteredMessage):
            self.game_mode = msg.gameMode
            if self.game_mode not in SUPPORTED_GAME_MODES:
                log.error(f"Unsupported game mode: {self.game_mode}")
                self.sendClose()
            else:
                log.info(f"Player {self.snake.name} was successfully registered!")
                log.info(f"Game mode: {self.game_mode}")

                if self.game_mode == GameMode.Tournament:
                    if not self.spoiler:
                        log.info("Disabling logs to prevent spoilers")
                        # FIXME: actually disable logs

                    self.is_tournament = True
                    self._send(create_heartbeat_request_message(msg.receivingPlayerId))

        async def _heartbeat_response(self, msg: HeartBeatResponseMessage):
            self.heart_beat = reactor.callLater(
                HEARTBEAT_INTERVAL / 1000,
                self._send,
                create_heartbeat_request_message(msg.receivingPlayerId),
            )

        def _game_link(self, msg: GameLinkEventMessage):
            log.info("Game is ready")
            self.url = msg.url

            if self.gameMode == GameMode.Training:
                self._send(create_start_game_message())

        async def _map_update(self, msg: MapUpdateEventMessage):
            game_map = GameMap(
                msg.map, msg.receivingPlayerId, self.game_settings, msg.gameTick
            )
            direction = await self.snake.get_next_move(game_map)
            self._send(
                create_register_move_message(
                    str(direction),
                    msg.receivingPlayerId,
                    msg.gameId,
                    msg.gameTick,
                )
            )

        def _snake_dead(self, msg: SnakeDeadEventMessage):
            if not self.spoiler:
                log.info(f"Snake died because: {msg.deathReason}")

        def _game_result(self, msg: GameResultEventMessage):
            log.info(f"Game result is in: {self.url}")

        def _game_ended(self, msg: GameEndedEventMessage):
            if self.spoiler:
                log.info(f"Game has ended. The winner was {msg.playerWinnerName}")

            if self.game_mode == GameMode.Training:
                self.sendClose()

        def _game_starting(self, msg: GameStartingEventMessage):
            log.info("Game is starting")
            log.info(f"Received updated game settings from server:")
            log.info(json.dumps(msg.gameSettings, indent=2))
            self.game_settings = msg.gameSettings

        def _invalid_player_name(self, msg: InvalidPlayerNameMessage):
            log.info(
                f"The player name {self.snake.name} was invalid, reason: {msg.reasonCode}"
            )
            self.sendClose()

        def _tournament_ended(self, msg: TournamentEndedMessage):
            log.info("Tournament has ended.")
            self.sendClose()

        def _no_active_tournament(self, msg: NoActiveTournamentMessage):
            log.info("No active tournament. Closing...")
            self.sendClose()

        def _invalid_arena_name(self, msg: InvalidPlayerNameMessage):
            log.info(f"There is no arena with the code: {self.venue}")
            self.sendClose()

        def _arena_is_full(self, msg: ArenaIsFullMessage):
            log.info(
                f"The arena {self.venue} is full, players connected: {msg.playersConnected}"
            )
            self.sendClose()

        def _invalid_message(self, msg: InvalidMessage):
            log.warn(msg.errorMessage)

        def _unrecognized_message(self, msg: Message):
            log.error(f"Received unrecognized message: {msg.type}")

    return SnakebotProtocol
