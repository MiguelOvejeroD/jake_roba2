import random


class PullRequestTypeHandler:

    whitelist = ['BuddyBuildTeam', 'despegar-dev', 'despegar-jenkins', 'drecom-jenkins', 'jenkinsCP',
                 'reddeafiliados-it', 'web-flow', 'Jenkins']

    def __init__(self, app, service, github_connector):
        self.app = app
        self.service = service
        self.github_connector = github_connector

    def will_handle(self, data):
        return 'commits' in data and len(data['commits']) > 0

    def handle(self, data):
        repo_owner = data['repository']['owner']['name']
        repo_name = data['repository']['name']
        commits = data['commits']

        for commit in commits:
            if 'username' in commit['committer'] and commit['committer']['username'] in self.whitelist:
                continue

            commit_info = self.github_connector.get_commit_info(repo_owner, repo_name, commit['id'])
            if 'commit' in commit_info:
                commit_data = commit_info['commit']
                is_squash_or_rebase = "users.noreply.github" in commit_data['author']['email'] \
                                      or "users.noreply.github" in commit_data['committer']['email']
                is_verified = commit_data['verification']['verified']
                if is_squash_or_rebase and not is_verified:
                    result = {
                        'username': commit_info['committer']['login'],
                        'email': commit_data['committer']['email'],
                        'sha': str(commit['id'])[:7],
                        'url': commit_info['html_url']
                    }
                    self.service.notify_pr_squash(repo_name, result)

    def check_commit(self, repo_owner, repo_name, commit_sha, committer):
        if committer in self.whitelist:
            return {'error': 'whitelisted'}

        commit_info = self.github_connector.get_commit_info(repo_owner, repo_name, commit_sha)
        if 'commit' not in commit_info:
            self.app.logger.warn("no-commit -> {info}".format(info=commit_info))
            return {'error': "no commit"}

        commit_data = commit_info['commit']
        return {
            'sha': str(commit_sha)[:7],
            'name': commit_data['committer']['name'],
            'email': commit_data['committer']['email'],
            'username': commit_info['committer']['login'],
            'url': commit_info['html_url'],
            'verified': commit_data['verification']['verified'],
            'reason': commit_data['verification']['reason'],
            'is_pr_squash': "users.noreply.github" in commit_data['author']['email']
                            or "users.noreply.github" in commit_data['committer']['email'],
            'notify': random.randint(0, 10) == 1
        } if ('error' not in commit_info) else commit_info
