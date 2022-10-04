import json

from flask import request, abort, Blueprint

from commons.connectors.SlackConnector import SlackConnector
from commons.utils.security import Security
from commons.controllers.FlaskController import FlaskController
from commons.connectors.GithubConnector import GithubConnector
from commons.connectors.NewRelicConnector import NewRelicConnector

from push_event.services.PushEventService import PushEventService
from push_event.handlers.CommitVerificationHandler import CommitVerificationHandler
from push_event.handlers.TagVerificationHandler import TagVerificationHandler
from push_event.handlers.FileEditVerificationHandler import FileEditVerificationHandler

from push_event.handlers.PullRequestTypeHandler import PullRequestTypeHandler

push_event = Blueprint('push_event', __name__)


@FlaskController.flask.route("/v3/github/hooks/push", methods=['POST'])
def push_made():
    FlaskController.app.logger.debug("Incoming request push made")
    pec = PushEventController()
    return pec.trigger_event()


class PushEventController():

    def __init__(self):
        self.app = FlaskController.app
        self.github_connector = GithubConnector(self.app)
        self.newrelic_connector = NewRelicConnector(self.app)
        self.push_event_service = PushEventService(self.app, self.newrelic_connector)
        self.slack_connector = SlackConnector(FlaskController.app)
        self.handlers = [
            CommitVerificationHandler(self.app, self.push_event_service, self.github_connector),
            PullRequestTypeHandler(self.app, self.push_event_service, self.github_connector),
            FileEditVerificationHandler(self.app, self.push_event_service, self.github_connector)
        ]

    def trigger_event(self):
        which_secret = self.app.config.get("git", "git_secret")
        secret = json.loads(self.app.config.get("vault", which_secret))
        ctx = self.app.context
        if ctx == "prod":
            hub_signature = request.headers['X_HUB_SIGNATURE']
        request_data = request.data
        if ctx == "prod" and not Security.verify_signature(request_data, hub_signature, secret["key"]):
            self.app.logger.warning("unauthorized request")
            message = "\n*Headers*\n```\n"
            for header in request.headers.keys():
                message += "{key}: {value}\n".format(key=header, value=request.headers.get(header))
            req_body = str(json.loads(request.data.decode("utf-8")))
            message += "```\n\n*Body*\n```\n{body}\n```".format(body=req_body)
            self.app.logger.warning("unauthorized request: "+message)
            self.slack_connector.send_attachment(channel='#jake',
                                                 pretext="The following request didn't pass the security check:",
                                                 username='Jake',
                                                 text=message,
                                                 fallback="Security Check Failed",
                                                 title="Security Check Failed",
                                                 color="warning")
            return 'Unauthorized', 401

        data = json.loads(request.data.decode("utf-8"))

        if 'hook_id' in data:
            return 'Ok', 200

        if self.app.context == "prod" and ('X-GitHub-Event' not in request.headers or request.headers['X-GitHub-Event'] != "push"):
            return 'Ok', 200

        self.app.logger.debug("start request: push event")

        repo_owner = data['repository']['owner']['name']
        repo_name = data['repository']['name']
        commits = data['commits']
        sender_name = data['sender']['login']
        sender_type = data['sender']['type']
        has_commits = len(commits) > 0

        has_no_committer = has_commits and ('username' not in commits[0]['committer'])
        self.newrelic_connector.record_metric("Hooks/Push", "pushed", 1, {
            'repo_owner': repo_owner,
            'repo_name': repo_name,
            'commits': len(commits),
            'sender': sender_name,
            'sender_type': sender_type,
            'no_committer': has_no_committer,
            'no_author': has_commits and ('username' not in commits[0]['author'])
        })

        for handler in self.handlers:
            if handler.will_handle(data):
                handler.handle(data)

        return 'Ok', 200

