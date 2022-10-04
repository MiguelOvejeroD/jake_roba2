import json
import re
import requests
from atpFlask.atp_flask import require_login
from commons.repositories.ATPGithubRepository import ATPGithubRepository
from github_to_ldap.services.Github2LdapService import Github2LdapService
from flask import Blueprint, render_template, Markup
from flask_cors import cross_origin, CORS
from commons.controllers.FlaskController import FlaskController

github_to_ldap = Blueprint('github_to_ldap', __name__)

CORS(FlaskController.app, resources=r'/github2ldap')

@FlaskController.flask.route("/github2ldap/api/users/<username>", methods=['GET'])
@cross_origin()
def github2ldap(username):
    FlaskController.app.logger.info("Incoming request github to ldap users")
    g2lc = Github2LdapController()
    return g2lc.triggerEvent(username)

@FlaskController.flask.route("/github2ldap", methods=['GET'])
@require_login(FlaskController.flask)
def github2ldapWeb():
    FlaskController.app.logger.info("Incoming request for github to ldap users web")
    g2lc = Github2LdapController()
    return g2lc.triggerEventWeb()

class Github2LdapController():

    def __init__(self):
        self.app = FlaskController.app
        self.github_to_ldap_service = Github2LdapService(self.app)
        self.atpgithub_repository = ATPGithubRepository(self.app)

    def triggerEvent(self, username):
        regex = re.compile("^[a-zA-Z0-9/-]*$")
        self.app.logger.debug("start request: github_to_ldap_user")
        if not regex.search(username):
            return "Wrong user"
        user = self.github_to_ldap_service.get_ldap_user(username)
        return json.dumps(user.__dict__)

    def triggerEventWeb(self):
        nevo = requests.get(self.app.config.get("nevo", "url"))
        header = nevo.json()['header']
        js = nevo.json()['js']
        css = nevo.json()['css']
        footer = nevo.json()['footer']
        return render_template('body.html', header=Markup(header), js=js, css=css, footer=Markup(footer), api_uri=self.app.config.get('api', 'uri'))
