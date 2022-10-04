import configparser
import logging
import os
from commons.connectors.VaultConnector import VaultConnector


class Application:

    def __init__(self):
        self.context = self.get_context()
        print("Reading configuration file for ", self.context)
        self.config = self.load_configuration()
        print("creating logger")
        self.logger = self.create_logger()
        # get credentials with Vault
        self.vaultConnector = VaultConnector(self)

    def get_context(self):
        try:
            f = open('/etc/cluster.context', 'r')
            context = f.readline()
            f.close()
        except OSError:
            context = "dev"
        return context

    def load_configuration(self):
        config = configparser.ConfigParser()
        config._interpolation = configparser.ExtendedInterpolation()
        # Read commons and later override with module config
        #config.read("conf/" + self.context + "/application.ini")
        config.read("app/conf/" + self.context + "/application.ini")
         #config.read(module+"/conf/" + self.context + "/application.ini")
        config['DEFAULT']['context'] = self.context
        #config['DEFAULT']['module'] = module
        return config

    def create_logger(self):
        logger = logging.getLogger("appsec")
        logger.info(" Setting logger level to %s ", self.config['DEFAULT']["logging.level"])
        logger.setLevel(logger_level(self.config['DEFAULT']["logging.level"]))
        if self.context == "prod":
            if not os.path.exists("logs"):
                os.makedirs("logs/")
            ch = logging.handlers.TimedRotatingFileHandler('./logs/app.log', when="D", interval=7)
        else:
            ch = logging.StreamHandler()
        ch.setLevel(logger_level(self.config['DEFAULT']["logging.level"]))
        ch.setFormatter(logging.Formatter(self.config['DEFAULT']["logging.format"]))
        logger.addHandler(ch)
        return logger

def logger_level(level):
    return {
        "CRITICAL": logging.CRITICAL,
        "FATAL":    logging.CRITICAL,
        "ERROR":    logging.ERROR,
        "WARNING":  logging.WARNING,
        "WARN":     logging.WARNING,
        "INFO":     logging.INFO,
        "DEBUG":    logging.DEBUG
    }[level]
