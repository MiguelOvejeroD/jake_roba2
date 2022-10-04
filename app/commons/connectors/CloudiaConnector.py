import requests
import json


class CloudiaConnector:

    def __init__(self, app):
        self.logger = app.logger
        self.config = app.config
        which_credentials = app.config.get("cloudia", "vault_credentials_key")
        self.credentials = json.loads(app.config.get("vault", which_credentials))

    def get_cluster_info(self, cluster):
        self.logger.debug(
            "get_cluster_info(%s): %s" %
            (cluster, self.config.get("cloudia", "cloudia-proxy.url") + 'cloud/clusters/' + cluster))
        r = requests.get(self.config.get("cloudia", "cloudia-proxy.url") + 'cloud/clusters/' + cluster,
                         auth=(self.credentials["user"], self.credentials["pass"]), verify=False)
        self.logger.debug("info: %s (%s)" % (r, r.content))
        if r.status_code == 200:
            return r.json()
        else:
            return {}
