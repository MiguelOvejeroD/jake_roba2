import http.client
import json
import os
import ssl


class VaultConnector:

    def __init__(self, app):
        self.logger = app.logger
        self.logger.info(" Communicating with Vault for secrets...")

        home_dir = os.path.expanduser('~')

        if app.context == "prod":
            app_id = open(os.path.join(home_dir, '.app_id'), 'r').readline().rstrip('\n')
            user_id = open(os.path.join(home_dir, '.user_id'), 'r').readline().rstrip('\n')
        else:
            app_id = open(os.path.join(home_dir, app.config.get('ids', 'app_id')), 'r').readline().rstrip('\n')
            user_id = open(os.path.join(home_dir, app.config.get('ids', 'user_id')), 'r').readline().rstrip('\n')

        self.headers = {"Accept": "application/json", "Content-Type": "application/json", "X-Endpoint": "vault"}
        self.auth = {"app_id": app_id, "user_id": user_id}

        # CAMIBOS TEMPORALES
        self.conn = http.client.HTTPSConnection(
            app.config.get("cloudia", "conductor-backend-ssl.host"), 443, context=ssl._create_unverified_context())
        for key, value in self.get_secrets(app).items():
            app.config["vault"][key] = value

        for key, value in self.get_secrets(app).items():
            app.config["vault"][key] = value

        #with open("/home/ignaciotruffat/sensitive.conf", "r") as sensfile:
            #for line in sensfile.readlines():
                #key =  line.split("=")[0]
                #value =  '='.join(line.split("=")[1:])
                #app.config["vault"][key] = value

    # curl -k -i -H "Accept: application/json" -H "Content-Type:application/json" -H "X-Endpoint:vault" -X POST
    # --data '{"app_id":"<ID>","user_id":"<ID>"}'
    # "https://proxy.despexds.net:443/v1/auth/app-id/login"
    def authenticate(self, app):
        self.conn.request("POST", app.config.get("vault", "auth.path"), json.dumps(self.auth), self.headers)
        resp = self.conn.getresponse()
        self.logger.debug("Vault authentication: (%s, %s)" % (resp.status, resp.reason))
        resp_json = json.loads(resp.read().decode("utf-8"))
        print(resp_json )
        return resp_json["auth"]["client_token"]

    # curl -k -i -H "Accept: application/json" -H "X-Vault-Token: <token>"
    # -H "X-Endpoint:vault" -X GET "https://proxy.despexds.net:443/v1/secret/namespaces/azkaban_jobs"
    def get_secrets(self, app):
        self.headers["X-Vault-Token"] = self.authenticate(app)
        self.conn.request("GET", app.config.get("vault", "secret.path"), None, self.headers)
        resp = self.conn.getresponse()
        self.logger.debug("Vault secret request: (%s, %s)" % (resp.status, resp.reason))
        resp_json = json.loads(resp.read().decode("utf-8"))
        self.conn.close()
        return resp_json["data"]
