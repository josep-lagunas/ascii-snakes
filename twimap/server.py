import logging
import os
import sys

from tornado.ioloop import IOLoop
from tornado.web import (
    Application,
)

from twimap.main import MainHandler
from twimap.real_time_websocket import RealTimeWebSocket

STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template")

logging.basicConfig(**{
    "format": "%(asctime)s %(message)s",
    "handlers": [
        logging.FileHandler(filename="log.log"),
        logging.StreamHandler(stream=sys.stdout)
    ],
    "encoding": "utf-8",
    "level": logging.INFO
})

settings = {
    "static_path": STATIC_PATH,
    "template_path": TEMPLATE_PATH,
}

HANDLERS = [
    ("/ws", RealTimeWebSocket, {"database": {"test": 123456}}),
    ("/", MainHandler, {"database": {"test": 123456}}),
]

app = Application(HANDLERS, **settings)

app.listen(9000)
IOLoop.current().start()
