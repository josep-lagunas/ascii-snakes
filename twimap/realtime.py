import json
import threading
from abc import ABC
from threading import Thread
from typing import Union, Optional, Awaitable, Any

from tornado import httputil
from tornado.websocket import WebSocketHandler
import tornado.web

from map_builder.map_api import MapApi
from map_traveller.map_traveller_api import MapTraveller


class EchoWebSocket(WebSocketHandler, ABC):

    def __init__(self,
                 application: tornado.web.Application,
                 request: httputil.HTTPServerRequest,
                 **kwargs: Any):
        super().__init__(application, request, **kwargs)
        self.semaphore = threading.Semaphore(1)

    def open(self):
        print("ws opened")

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        try:
            data = json.loads(message)
        except Exception as exc:
            print(exc)
            data = {}
        rows = data.get("rows", 10)
        cols = data.get("cols", 10)
        delay = data.get("delay", 0.02)
        apply_restrictions = data.get("apply_restrictions", True)
        travellers_count = data.get("travellers_count", 1)
        wall_type = data.get("wall_type", 0)
        map_api = MapApi(lambda m, p: self.w(json.dumps({"description": m, "progress": p})))
        str_map = map_api.build_map(rows=rows, cols=cols, restricted=apply_restrictions, wall_type=wall_type)

        self.w(json.dumps({"map": str_map}))

        call_traveller_progress = lambda p: self.w(json.dumps(p))

        for i in range(travellers_count):
            traveller = Thread(target=MapTraveller.initialize_traveller, args=(map_api.map, call_traveller_progress,
                                                                               delay,))
            traveller.start()

    def on_close(self):
        ("ws closed")

    def w(self, content: str) -> None:
        self.semaphore.acquire()
        self.write_message(content)
        self.semaphore.release()
