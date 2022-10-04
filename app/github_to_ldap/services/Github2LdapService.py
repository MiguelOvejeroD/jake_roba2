import re
from collections import OrderedDict
from commons.repositories.ATPGithubRepository import ATPGithubRepository
from commons.connectors.LDAPConnector import LDAPConnector
from github_to_ldap.model.User import User


class Github2LdapService:

    def __init__(self, app):
        self.logger = app.logger
        self.config = app.config
        self.atpgithub_repository = ATPGithubRepository(app)
        self.ldap_connector = LDAPConnector(app)

    def get_ldap_user(self, username):
        self.logger.debug("retrieving atp user")
        user = User(git=username)
        user.atp_user = self.atpgithub_repository.get_atp_user_by_github_user(user.git_user)
        if not user.atp_user:
            user.set_valid(False)
            user.set_comment("ATP user not found")
            return user
        attr = re.split(";|,", self.config.get("ldap", "query.attributes"))
        attributes = list(OrderedDict.fromkeys(attr).keys())
        ldap_response = self.ldap_connector.find("(userPrincipalName=" + user.atp_user + ")", attributes=attributes)
        if ldap_response == []:
            user.set_valid(False)
            user.set_comment("LDAP user not found")
            return user
        #convierto a lista la unica tupla devuelta
        ldap_response = list(ldap_response[0])
        user.set_ldap_user(ldap_response[0])
        user.set_account_control_code(ldap_response[2])
        user.set_valid(True)
        return user

    def get_repo_data(self, data):
        rdata = {}
        rdata['username'] = data["sender"]["login"]
        rdata['name'] = data["repository"]["name"]
        rdata['url'] = data["repository"]["html_url"]
        rdata['status'] = data['action']
        return rdata