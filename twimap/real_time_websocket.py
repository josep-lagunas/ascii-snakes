import asyncio
import json
import logging
from abc import ABC
from asyncio import Future
from typing import Union, Optional, Awaitable, Any, Dict, Callable

import tornado.web
from tornado import httputil
from tornado.websocket import WebSocketHandler, WebSocketClosedError

from map_builder.map_api import MapApi
from map_traveller.world_traveler_api import WorldTraveler as WorldTravelerRec
from map_traveller.world_traveler_api_v2 import WorldTraveler
from twimap.cancel_token import CancelToken

logger = logging.getLogger(__name__)


class RealTimeWebSocket(WebSocketHandler, ABC):

    def __init__(self,
                 application: tornado.web.Application,
                 request: httputil.HTTPServerRequest,
                 **kwargs: Any):
        self.database = None
        super().__init__(application, request, **kwargs)
        self._cancel_token = CancelToken()
        self._travelers_count = 0
        self._travelers_total_count = 0

    def initialize(self, database: dict) -> None:
        self.database = database

    def open(self, *args, **kwargs):
        [logger.info("***") for i in range(2)]
        logger.info(f"Websocket connection [{id(self.ws_connection)}] opened")
        cancellation_token_info = "Cancellation token [{}] ready, is_cancelled: [{}]"
        logger.info(str.format(cancellation_token_info, id(self._cancel_token), self._cancel_token.is_cancelled))

    async def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        try:
            data = json.loads(message)
        except Exception as exc:
            logger.info(exc)
            data = {}
        rows = data.get("rows", 3)
        cols = data.get("cols", 10)
        delay_range = data.get("delay_range", {"min": 0.01, "max": 0.5})
        snakes_size = data.get("snakes_size", {"min": 1, "max": 10})
        apply_restrictions = data.get("apply_restrictions", True)
        travellers_count = data.get("travellers_count", 1)
        self._travelers_total_count = travellers_count
        wall_type = data.get("wall_type", 0)

        world_generation_progress: Callable[[int, str, str], Future[None]] = lambda row, line, progress: (
            self.write_message(
                json.dumps(
                    {
                        "row":
                            {
                                "index": row,
                                "content": line,
                            },
                        "progress": progress
                    }
                )
            )
        )
        map_api = MapApi(progress_creation_callback=world_generation_progress, cancel_token=self._cancel_token)
        world_created = await map_api.build_map(
            rows=rows, cols=cols, restricted=apply_restrictions, wall_type=wall_type
        )

        if not world_created:
            return

        call_traveler_progress: Callable[[Any], Future[None]] = lambda p: self.write_message(json.dumps(p))
        logger.info(f"starting {travellers_count} travelers...")
        travelers_rec = [
            WorldTravelerRec.initialize_traveller(
                str(i),
                map_api.map,
                snakes_size,
                call_traveler_progress,
                self._on_traveler_initialized,
                delay_range,
                self._cancel_token,
            )
            for i in range(int(travellers_count/2))
            if not self._cancel_token.is_cancelled
        ]
        travelers_iter = [
            WorldTraveler.initialize_traveller(
                str(i),
                map_api.map,
                snakes_size,
                call_traveler_progress,
                self._on_traveler_initialized,
                delay_range,
                self._cancel_token,
            )
            for i in range(int(travellers_count/2) + travellers_count % 2)
            if not self._cancel_token.is_cancelled
        ]
        travelers = travelers_rec + travelers_iter

        await asyncio.gather(*travelers)
        logger.info("All finished!!!!!")
        return

    def _on_traveler_initialized(self):
        self._travelers_count += 1
        self.write_message(
            {
                "type": "travelerInit",
                "travelersInitializedCount": self._travelers_count,
                "totalTravelersCount": self._travelers_total_count
            })

    def on_connection_close(self) -> None:
        logger.info(f"on_connection_close handler, Websocket connection [{id(self.ws_connection)}] ready to be closed")
        super().on_connection_close()

    def on_close(self) -> None:
        logger.info(f"on_close handler, Websocket connection already closed")

    def write_message(
            self, message: Union[bytes, str, Dict[str, Any]], binary: bool = False
    ) -> "Future[None]":
        if self.ws_connection.is_closing():
            if not self._cancel_token.is_cancelled:
                self._cancel_token.cancel()
                logger.info(f"Cancellation token [{id(self._cancel_token)}] activated, "
                      f"is_cancelled: [{self._cancel_token.is_cancelled}]")
            fut: Future[None] = asyncio.Future()
            fut.set_result(None)
            return fut

        task = super().write_message(message, binary)

        async def wrapper() -> None:
            try:
                if task:
                    await task
            except WebSocketClosedError:
                pass
            finally:
                if task and task.done() and not task.cancelled():
                    task.exception()

        return asyncio.ensure_future(wrapper())
