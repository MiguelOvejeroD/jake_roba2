import json
import traceback
from commons.repositories.ATPGithubRepository import ATPGithubRepository
from project_event.services.ProjectCreateService import ProjectCreateService
from flask import request, abort, Blueprint
from commons.utils.security import Security
from commons.controllers.FlaskController import FlaskController
import requests


repo_event = Blueprint('repo_event', __name__)

@FlaskController.flask.route("/v3/github/hooks/projects/create", methods=['POST'])
def repo_created():
    FlaskController.app.logger.debug("Incoming request repo created")
    pec = ProjectEventController()
    return pec.triggerEvent()

class ProjectEventController():

    def __init__(self):
        self.app = FlaskController.app
        self.project_create_service = ProjectCreateService(self.app)
        self.atpgithub_repository = ATPGithubRepository(self.app)

    #existen varios eventos que involucran a un proyecto que podrian triggerear un push desde github ("created", "edited", "closed", "reopened", "deleted".)
    #con este discriminador podría tratarse cada uno individualmente
    def func(self, action):
        return{
            "created": "repo_created",
            "deleted": "repo_deleted",
            "publicized": "repo_publicized",
            "privatized": "repo_privatized",
            "archived": "repo_archived",
            "unarchived": "repo_unarchived"
        }[action]


    def triggerEvent(self):
        which_secret = self.app.config.get("git", "git_secret")
        secret = json.loads(self.app.config.get("vault", which_secret))
        if (self.app.context == "prod" and not Security.verify_signature(request.data, request.headers['X_HUB_SIGNATURE'], secret["key"])):
            return 'Unauthorized', 401
        self.app.logger.debug("start request: project event")
        data = json.loads(request.data.decode("utf-8"))
        return getattr(self, self.func(data["action"]))(data, request.headers)


    def get_repo_data(self, data):
        rdata = {}
        rdata['username'] = data["sender"]["login"]
        rdata['name'] = data["repository"]["name"]
        rdata['url'] = data["repository"]["html_url"]
        rdata['status'] = data['action']
        return rdata


    def repo_publicized(self, data, headers = None):
        return "OK", 204

    def repo_privatized(self, data, headers = None):
        return "OK", 204

    def repo_archived(self, data, headers = None):
        return "OK", 204

    def repo_unarchived(self, data, headers = None):
        return "OK", 204


    def repo_deleted(self, data, headers = []):
        rdata = self.get_repo_data(data)
        self.app.logger.debug("event triggered: repository %s by %s" % (rdata['status'], rdata['username']))
        atpuser = self.atpgithub_repository.get_atp_user_by_github_user(rdata['username'])
        if atpuser == False:
            self.app.logger.error("ATP user for %s not found" % rdata['username'])
            return "User not found", 204
        ldapuser = self.project_create_service.get_ldap_user(atpuser)
        if ldapuser == []:
            self.app.logger.error("LDAP user for %s not found" % atpuser)
            return "User not found", 204
        self.project_create_service.project_deleted(rdata['url'])
        return 'OK', 200

    def repo_modified(self, data, headers = []):
        rdata = self.get_repo_data(data)
        self.app.logger.debug("event triggered: repository %s by %s" % (rdata['status'], rdata['username']))
        self.project_create_service.project_modified(rdata['url'], rdata['status'])
        return "OK", 200

    def repo_created(self, data, headers = []):
        rdata = self.get_repo_data(data)
        self.app.logger.debug("event triggered: repository created by %s" % rdata['username'])
        atpuser = self.atpgithub_repository.get_atp_user_by_github_user(rdata['username'])
        if atpuser == False:
            self.app.logger.error("ATP user for %s not found" % rdata['username'])
            return "User not found", 204
        ldapuser = self.project_create_service.get_ldap_user(atpuser)
        if ldapuser == []:
            self.app.logger.error("LDAP user for %s not found" % atpuser)
            return "User not found", 204
        ldapuser_email = ldapuser[0][0]
        self.app.logger.debug("sending email to %s" % ldapuser_email)

        url = rdata['url']

        self.project_create_service.send_email_to(ldapuser_email, rdata['url'])
        self.app.logger.debug("adding row to sheets %s %s %s" % (rdata['url'], rdata['name'], ldapuser_email))
        self.project_create_service.project_created(rdata['name'], rdata['url'], rdata['status'], 'F', ldapuser_email)
        return "OK", 200
