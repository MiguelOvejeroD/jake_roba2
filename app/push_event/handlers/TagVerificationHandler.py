import random


class TagVerificationHandler:

    whitelist = ['BuddyBuildTeam', 'despegar-dev', 'despegar-jenkins', 'drecom-jenkins', 'jenkinsCP',
                 'reddeafiliados-it', 'web-flow', 'Jenkins']

    def __init__(self, app, service, github_connector):
        self.app = app
        self.service = service
        self.github_connector = github_connector

    def will_handle(self, data):
        return 'commits' in data and len(data['commits']) > 0

    def handle(self, data):
        repo_owner = data['repository']['owner']['name']
        repo_name = data['repository']['name']
        tag_info = self.github_connector.get_tag_info(repo_owner, repo_name, data['after'])
        pass
