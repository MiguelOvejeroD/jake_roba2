import configparser
from pymongo import MongoClient

class MongoRepository:

    def __init__(self, app):
        self.config = app.config

    def get_connection(self):
        return MongoClient(self.config.get("mongo", "host"),int(self.config.get("mongo", "port")))
