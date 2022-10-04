from commons.repositories.MongoRepository import MongoRepository
from github_to_ldap.model.User import User


class ATPGithubRepository(MongoRepository):

    def __init__(self, app):
        self.client = MongoRepository(app).get_connection()
        self.logger = app.logger
        self.config = app.config


    def get_atp_user_by_github_user(self, user):
        try:
            user = user.lower()
            self.logger.debug("fetching ATP user's information from user: %s" % user)
            users = self.client[self.config.get("mongo", "db")][self.config.get("mongo", "collection")]
            user = users.find_one({"githubUsername" : user})
            if user == None:
                return False
            return user['_id']
        except Exception as e:
            self.logger.error("error fetching user's email")
            self.logger.error(str(e))
            return False