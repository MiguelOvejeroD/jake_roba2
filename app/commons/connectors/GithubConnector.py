import http.client
import json
import ssl
import time


class GithubConnector:

    MAX_RETRIES = 3

    NOT_FOUND = {
        'error': 'Not Found'
    }

    def __init__(self, app):
        self.app = app
        which_pakey = app.config.get("github", "vault_credentials_key")
        pakey = json.loads(app.config.get("vault", which_pakey))
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.app.config.get("github", "user-agent"),
            "Authorization": "token %s" % pakey['key']
        }
        self.conn = http.client.HTTPSConnection(
            self.app.config.get("github", "host"), 443, context=ssl._create_unverified_context()
        )

    def get_tag_info(self, repo_owner, repo_name, tag_sha):
        url = self.app.config.get("github", "tag-info.url") % (repo_owner, repo_name, tag_sha)
        return self.get_tag_info_by_url(url)

    def get_tag_info_by_url(self, url):
        self.conn.request("GET", url, None, self.headers)
        resp = self.conn.getresponse()
        resp_json = json.loads(resp.read().decode("utf-8"))
        if 'message' in resp_json:
            if resp_json['message'] == 'Moved Permanently':
                return self.get_tag_info_by_url(resp_json['url']) if 'url' in resp_json else self.NOT_FOUND
            elif resp_json['message'] == 'Not Found':
                return self.NOT_FOUND
        self.conn.close()
        return resp_json

    def get_commit_info(self, repo_owner, repo_name, commit_sha):
        url = self.build_request_url(repo_owner, repo_name, commit_sha)
        return self.get_commit_info_by_url(url)

    def get_commit_info_by_url(self, url):
        for i in range(self.MAX_RETRIES):
            try:
                self.conn.request("GET", url, None, self.headers)
                resp = self.conn.getresponse()
                resp_json = json.loads(resp.read().decode("utf-8"))
                if 'message' in resp_json:
                    if resp_json['message'] == 'Moved Permanently':
                        return self.get_commit_info_by_url(resp_json['url']) if 'url' in resp_json else self.NOT_FOUND
                    elif resp_json['message'] == 'Not Found':
                        return self.NOT_FOUND
                self.conn.close()
            except TimeoutError as e:
                if i == self.MAX_RETRIES:
                    raise e
                continue
            else:
                break
        return resp_json

    def build_request_url(self, repo_owner, repo_name, commit_sha):
        return self.app.config.get("github", "commit-info.url") % (repo_owner, repo_name, commit_sha)