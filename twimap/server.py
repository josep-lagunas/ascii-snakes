import os

from tornado.web import (
    Application,
)
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler

from twimap.main import MainHandler
from twimap.realtime import EchoWebSocket

STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template")

settings = {
    "static_path": STATIC_PATH,
    "template_path": TEMPLATE_PATH,
}

HANDLERS = [
    ("/ws", EchoWebSocket),
    ("/", MainHandler),
]

app = Application(HANDLERS, **settings)

app.listen(8888)
IOLoop.current().start()
