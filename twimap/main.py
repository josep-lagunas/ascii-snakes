from tornado.web import RequestHandler


class MainHandler(RequestHandler):
    def initialize(self, database) -> None:
        self.database = database

    def get(self):
        self.render("index.html")
