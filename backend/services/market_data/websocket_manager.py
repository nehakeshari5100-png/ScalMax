import asyncio
import json
import time
import logging
from typing import Callable, Dict, List, Optional, Set, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


class WebSocketManager:
    def __init__(
        self,
        name: str,
        max_reconnect_delay: float = 60.0,
        initial_reconnect_delay: float = 1.0,
        ping_interval: int = 20,
        ping_timeout: int = 10,
    ):
        self.name = name
        self._state = ConnectionState.DISCONNECTED
        self._ws = None
        self._url: Optional[str] = None
        self._on_message: Optional[Callable] = None
        self._on_connect: Optional[Callable] = None
        self._on_disconnect: Optional[Callable] = None
        self._subscriptions: List[Dict] = []
        self._reconnect_delay = initial_reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._task: Optional[asyncio.Task] = None
        self._should_run = False
        self._last_message_time: float = 0
        self._latency: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def latency_ms(self) -> Optional[float]:
        return self._latency

    def on_message(self, callback: Callable):
        self._on_message = callback

    def on_connect(self, callback: Callable):
        self._on_connect = callback

    def on_disconnect(self, callback: Callable):
        self._on_disconnect = callback

    async def connect(self, url: str, subscriptions: Optional[List[Dict]] = None):
        self._url = url
        if subscriptions:
            self._subscriptions = subscriptions
        self._should_run = True
        self._task = asyncio.create_task(self._run())

    async def disconnect(self):
        self._should_run = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._close_ws()
        self._state = ConnectionState.CLOSED

    async def send(self, data: dict):
        async with self._lock:
            if self._ws and self._state == ConnectionState.CONNECTED:
                try:
                    await self._ws.send(json.dumps(data))
                except Exception as e:
                    logger.warning(f"[{self.name}] Send error: {e}")

    async def subscribe(self, subscription: Dict):
        self._subscriptions.append(subscription)
        if self._state == ConnectionState.CONNECTED:
            await self.send(subscription)

    async def _run(self):
        while self._should_run:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.name}] Connection error: {e}")
                self._state = ConnectionState.DISCONNECTED
                await self._notify_disconnect()

            if not self._should_run:
                break

            await self._wait_before_reconnect()

    async def _connect_and_listen(self):
        import websockets

        self._state = ConnectionState.CONNECTING
        logger.info(f"[{self.name}] Connecting to {self._url}")

        try:
            self._ws = await websockets.connect(
                self._url,
                ping_interval=self._ping_interval,
                ping_timeout=self._ping_timeout,
                close_timeout=5,
                max_size=10_485_760,
            )

            self._state = ConnectionState.CONNECTED
            self._reconnect_delay = 1.0
            self._last_message_time = time.time()
            logger.info(f"[{self.name}] Connected")

            await self._send_subscriptions()
            await self._notify_connect()

            await self._listen_loop()

        except (websockets.exceptions.WebSocketException, OSError) as e:
            logger.warning(f"[{self.name}] Connection failed: {e}")
            raise

    async def _listen_loop(self):
        import websockets

        while self._should_run and self._ws:
            try:
                message = await asyncio.wait_for(
                    self._ws.recv(),
                    timeout=self._ping_interval + 5,
                )
                self._last_message_time = time.time()

                if self._on_message:
                    try:
                        data = json.loads(message)
                        self._on_message(data)
                    except json.JSONDecodeError:
                        pass

            except asyncio.TimeoutError:
                if self._ws:
                    try:
                        pong = await self._ws.ping()
                        await asyncio.wait_for(pong, timeout=10)
                    except Exception:
                        logger.warning(f"[{self.name}] Ping timeout")
                        break
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"[{self.name}] Connection closed")
                break
            except Exception as e:
                logger.error(f"[{self.name}] Listen error: {e}")
                break

    async def _send_subscriptions(self):
        if not self._subscriptions:
            return
        for sub in self._subscriptions:
            try:
                await self.send(sub)
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.warning(f"[{self.name}] Subscribe error: {e}")

    async def _close_ws(self):
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _wait_before_reconnect(self):
        self._state = ConnectionState.RECONNECTING
        delay = min(self._reconnect_delay, self._max_reconnect_delay)
        self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
        logger.info(f"[{self.name}] Reconnecting in {delay:.1f}s...")
        await asyncio.sleep(delay)

    async def _notify_connect(self):
        if self._on_connect:
            try:
                self._on_connect()
            except Exception as e:
                logger.error(f"[{self.name}] on_connect error: {e}")

    async def _notify_disconnect(self):
        if self._on_disconnect:
            try:
                self._on_disconnect()
            except Exception as e:
                logger.error(f"[{self.name}] on_disconnect error: {e}")

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "state": self._state.value,
            "latency_ms": self._latency,
            "subscriptions": len(self._subscriptions),
            "last_message_ago": time.time() - self._last_message_time if self._last_message_time else None,
        }
