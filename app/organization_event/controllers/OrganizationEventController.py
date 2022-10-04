import json
from commons.repositories.ATPGithubRepository import ATPGithubRepository
from project_event.services.ProjectCreateService import ProjectCreateService
from organization_event.services.OrganizationEventService import OrganizationEventService
from flask import request, abort, Blueprint
from commons.utils.security import Security
from commons.controllers.FlaskController import FlaskController


org_event = Blueprint('org_event', __name__)

@FlaskController.flask.route("/v3/github/hooks/organization/action", methods=['POST'])
def action_event():
    FlaskController.app.logger.debug("Incoming request: organization action")
    oec = OrganizationEventController()
    return oec.trigger_event()

class OrganizationEventController():

    def __init__(self):
        self.app = FlaskController.app
        self.organization_event_service = OrganizationEventService(self.app)
        self.atpgithub_repository = ATPGithubRepository(self.app)

    def func(self, action):
        return{
            "member_added": "member_added",
            "member_removed": "member_removed",
            "member_invited": "member_invited"
        }[action]

    def trigger_event(self):
        which_secret = self.app.config.get("git", "git_secret")
        secret = json.loads(self.app.config.get("vault", which_secret))
        if (self.app.context == "prod" and not Security.verify_signature(request.data,
                                                                         request.headers['X_HUB_SIGNATURE'],
                                                                         secret["key"])):
            self.app.logger.warning("unauthorized request")
            message = "\n*Headers*\n```\n"
            for header in request.headers.keys():
                message += "{key}: {value}\n".format(key=header, value=request.headers.get(header))
            req_body = str(json.loads(request.data.decode("utf-8")))
            message += "```\n\n*Body*\n```\n{body}\n```".format(body=req_body)
            self.app.logger.warning("unauthorized request: " + message)
            self.slack_connector.send_attachment(channel='#jake',
                                                 pretext="The following request didn't pass the security check:",
                                                 username='Jake',
                                                 text=message,
                                                 fallback="Security Check Failed",
                                                 title="Security Check Failed",
                                                 color="warning")
            return 'Unauthorized', 401
        data = json.loads(request.data.decode("utf-8"))
        self.app.logger.info("start request: organization event")
        if 'hook_id' in data:
            return 'OK', 200

        return getattr(self, self.func(data["action"]))(data, request.headers)

    def member_added(self, data, headers = None):
        """if 'membership' in data:
            addedUsr = data['membership']['user']['login']
            self.app.logger.info('user added to organization: '+addedUsr)
            if not self.atpgithub_repository.get_atp_user_by_github_user(addedUsr):
                usrEmail = data['invitation']['email']
                if usrEmail:
                    self.app.logger.info('sending email to user: '+usrEmail)
                    self.organization_event_service.send_user_email(usrEmail, addedUsr)
                else:
                    sender = data['sender']['login']
                    self.app.logger.info('sending email to invitation sender: '+sender)
                    sender_atp_usr = self.atpgithub_repository.get_atp_user_by_github_user(sender)
                    if sender_atp_usr:
                        ldapuser = self.organization_event_service.get_ldap_user(sender_atp_usr)
                        self.organization_event_service.send_sender_email(ldapuser[0][0], addedUsr)
                    else:
                        self.organization_event_service.send_appsec_email(addedUsr, sender)
            self.app.logger.info('user alreaday in ATP')
            return "OK", 200"""
        return "OK", 200

    def member_removed(self, data, headers = None):
        return "OK", 200

    def member_invited(self, data, headers = None):
        return "OK", 200
