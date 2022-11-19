import json
from abc import ABC
from typing import Union, Optional, Awaitable

from tornado.websocket import WebSocketHandler

from map_builder.map_api import MapApi


class EchoWebSocket(WebSocketHandler, ABC):
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
        apply_restrictions = data.get("apply_restrictions", True)
        wall_type = data.get("wall_type", 0)
        map_api = MapApi(lambda m, p: self.w(json.dumps({"description": m, "progress": p})))
        message = map_api.build_map(rows=rows, cols=cols, restricted=apply_restrictions, wall_type=wall_type)

        self.w(json.dumps({"map": message}))

    def on_close(self):
        print("ws closed")

    def w(self, content: str) -> None:
        self.write_message(content)
