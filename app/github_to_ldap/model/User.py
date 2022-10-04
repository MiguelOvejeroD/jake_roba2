class User:

    active_codes = ['2080','66048','512','66080','544']

    def __init__(self, git=None, atp=None, ldap=None, active=None, account_code=None, valid=None, comment=None):
        self.git_user = git
        self.atp_user = atp
        self.ldap_user = ldap
        self.active = active
        self.account_control_code = account_code
        self.valid = valid
        self.comment = comment

    def set_account_control_code(self, account_code):
        self.account_control_code = account_code
        self.active = account_code in User.active_codes

    def get_account_control_code(self):
        return self.account_control_code

    def set_git_user(self,git_user):
        self.git_user = git_user

    def get_git_user(self):
        return self.git_user

    def set_atp_user(self,atp_user):
        self.atp_user = atp_user

    def get_atp_user(self):
        return self.atp_user

    def set_ldap_user(self,ldap_user):
        self.ldap_user = ldap_user

    def get_ldap_user(self):
        return self.ldap_user

    def is_active(self):
        return self.active

    def set_valid(self, valid):
        self.valid = valid

    def is_valid(self):
        return self.valid

    def set_comment(self, comment):
        self.comment = comment

    def get_comment(self):
        return self.comment