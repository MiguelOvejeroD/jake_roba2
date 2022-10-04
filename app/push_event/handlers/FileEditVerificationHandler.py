import logging, logging.handlers

from commons.controllers.FlaskController import FlaskController
from commons.utils.UDPLoggerHandler import UDPLoggerHandler

class FileEditVerificationHandler:

    whitelist = ['BuddyBuildTeam', 'despegar-dev', 'despegar-jenkins', 'drecom-jenkins', 'jenkinsCP',
                 'reddeafiliados-it', 'web-flow', 'Jenkins']

    file_whitelist = ['pom.xml', 'package.json', 'package-lock.json', 'build.sbt', 'version.sbt', 'application.conf']

    repository_whitelist = ['ra-jenkins']

    def __init__(self, app, service, github_connector):
        self.app = app
        self.service = service
        self.github_connector = github_connector
        self.whitelist = list(map(lambda x: x.strip(), app.config.get('bots', 'botlist').split(',')))
        self.logger = None
        self.log_message = None

    def will_handle(self, data):
        return self.is_bot_commit(data)

    def handle(self, hookdata):
        self.app.logger.info("handling file edit verification")
        repository = hookdata['repository']['name']
        owner = hookdata['repository']['owner']['name']
        pusher = hookdata['pusher']
        bot_commits = list(filter(lambda commit: ('username' in commit['author'] and commit['author']['username'] in self.whitelist) or ('username' in commit['committer'] and commit['committer']['username'] in self.whitelist), hookdata['commits']))

        for commit in bot_commits:
            committer_info = commit['committer']
            author_info = commit['author']
            #get_commit_info trae mas info del commit de la que dispongo hasta ahora, conservo solo la informacion del commiter y el author y pido la info completa del commit
            #commit_info = self.github_connector.get_commit_info(owner, repository, '5f1183a19839da0227525151305292750005edf3')
            commit_info = self.github_connector.get_commit_info(owner, repository, commit['id'])
            self.log_commit(commit_info, author_info, committer_info, pusher)
            if self.must_check_files(repository):
                self.check_files_modified(commit_info)


    def must_check_files(self, repository):
        return repository not in self.repository_whitelist

    def is_bot_commit(self, data):
        self.app.logger.debug('checking if commit was made by bot')
        for c in data['commits']:
            if (('username' in c['author'] and c['author']['username'] in self.whitelist) or ('username' in c['committer'] and c['committer']['username'] in self.whitelist)):
                return True
        return False

    def check_files_modified(self, commit = None):
        pretext = "The user despegar-jenkins has modified some files outside the whitelist:"
        title = "Jenkins File Modification Alert"
        message = ""
        for file in commit['files']:
            alert = True
            #por cada archivo modificado deberia entrar en este if, si en algun caso no entra entonces alerta
            if any(f in file['filename'] for f in self.file_whitelist):
                alert = False
            if alert:
                message += "\n> <" + str(commit['html_url']) + "|" + str(commit['sha']) \
                           + ">\n>  " + file['filename'] + """\n"""
        if (message != ""):
            self.app.logger.info("Alert message: "+message)
            FlaskController.alert(message, pretext, title)

    def log_commit(self, commit = None, author_info = None, committer_info = None, pusher = None):
        # TODO START 19/07 HOTFIX
        if 'sha' not in commit:
            return
        # TODO END 19/07 HOTFIX

        try:
            self.app.logger.debug('logging commit: '+commit['sha'])
            self.logger = self.create_logger_udp()
            self.log_message = ""
            self.log_message += commit['sha'] +' - pusher: '+str(pusher)
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - webhook - author: '+str(author_info)
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - webhook - commiter: ' + str(committer_info)
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - sha: ' + str(commit['sha'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - html_url: ' + str(commit['html_url'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - commit - author: ' + str(commit['commit']['author'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - commit - committer: ' + str(commit['commit']['committer'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - message: ' + str(commit['commit']['message'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - verification: ' + str(commit['commit']['verification'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - author - login: ' + str(commit['author']['login'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - author - id: ' + str(commit['author']['id'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - committer - login: ' + str(commit['committer']['login'])
            self.logger.info(self.log_message)
            self.log_message = commit['sha'] +' - committer - id: ' + str(commit['committer']['id'])
            self.logger.info(self.log_message)

            for file in commit['files']:
                self.log_message = commit['sha'] +' - filename: '+file['filename']+" - "+ file['status'] + "\n"
                if 'patch' in file:
                    self.log_message += file['patch']
                    self.logger.info(self.log_message)
        finally:
            self.logger.handlers = []


    def create_logger_udp(self):
        if self.logger == None:
            host = self.app.config['logging']['instance']
            port = self.app.config['logging']['port']
            udp_logger = logging.getLogger(host)
            udp_logger.setLevel(logger_level("INFO"))
            dh = UDPLoggerHandler(host, int(port))
            dh.setLevel(logger_level("INFO"))
            dh.setFormatter(logging.Formatter(self.app.config['DEFAULT']["logging.format"]))
            udp_logger.addHandler(dh)
        else:
            udp_logger = self.logger
        return udp_logger

def logger_level(level):
    return {
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG
    }[level]

