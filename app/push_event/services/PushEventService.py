# coding=utf-8
import os.path

import newrelic.agent

from commons.connectors.SMTPConnector import SMTPConnector
from commons.connectors.LDAPConnector import LDAPConnector
from commons.repositories.ATPGithubRepository import ATPGithubRepository
from project_event.services.ProjectCreateService import ProjectCreateService


class PushEventService:

    def __init__(self, app, newrelic_connector):
        self.app = app
        self.logger = app.logger
        self.config = app.config
        self.smtp_connector = SMTPConnector(app)
        self.ldap_connector = LDAPConnector(app)
        self.atpgithub_repository = ATPGithubRepository(app)
        self.project_create_service = ProjectCreateService(app)
        self.newrelic_connector = newrelic_connector

    @newrelic.agent.background_task(name="user_notification", group="Task")
    def notify_user(self, repo_name, result):
        self.newrelic_connector.record_event("User_Notified", "notified", result)
        user_email = self.get_user_email(result['username'])
        if 'error' in user_email:
            return
        self.app.logger.debug("Sent notification email to {email}".format(email=user_email))
        self.send_email_notification(
            user_email if user_email != "" else result['email'],
            repo_name, result['sha'], result['url'])

    @newrelic.agent.background_task(name="user_notification", group="Task")
    def notify_pr_squash(self, repo_name, result):
        self.newrelic_connector.record_event("Squash_Notified", "notified", result)
        user_email = self.get_user_email(result['username'])
        if 'error' in user_email:
            return
        self.app.logger.debug("Sent squash notification email to {email}".format(email=user_email))
        self.send_squash_email_notification(
            user_email if user_email != "" else result['email'],
            repo_name, result['sha'], result['url'])

    def get_user_email(self, github_username):
        atp_user = self.atpgithub_repository.get_atp_user_by_github_user(github_username)
        if not atp_user:
            self.app.logger.error("ATP user for %s not found" % github_username)
            return {"error": "ATP user for %s not found" % github_username}
        ldap_user = self.project_create_service.get_ldap_user(atp_user)
        if not ldap_user:
            self.app.logger.error("LDAP user for %s not found" % atp_user)
            return {"error": "LDAP user for %s not found" % atp_user}
        ldapuser_email = ldap_user[0][0]
        return ldapuser_email

    def send_email_notification(self, to, repo_name, commit_sha, commit_url):
        self.logger.debug("""
        Sending unverified commit notification email:
            To: {email}
            Repo: {repo}
            Commit: {sha}""".format(email=to, sha=commit_sha, repo=repo_name))
        message = """
            <p>Por políticas de Seguridad Informática se requiere que los commits estén verificados por una clave GPG personal.</p>
            
            <p><strong>Detectamos que tu commit <a href="{url}" target="_blank">#{sha}</a> no está verificado.<strong></p>
            
            <p>En adelante, por favor verificá sus commits utilizando el siguiente tutorial:
            <a href="https://github.com/despegar/test-signed-commits" target="_blank">github.com/despegar/test-signed-commits</a></p>
        """.format(sha=commit_sha, url=commit_url)

        self.smtp_connector.send_email(to=[to],
                                       subject='Sobre tu commit #{sha} en {repo}'.format(sha=commit_sha, repo=repo_name),
                                       message=message)

    def send_squash_email_notification(self, to, repo_name, commit_sha, commit_url):
        self.logger.debug("""
        Sending unverified commit notification email:
            To: {email}
            Repo: {repo}
            Commit: {sha}""".format(email=to, sha=commit_sha, repo=repo_name))
        message = """
            <p><strong>Detectamos que el commit <a href="{url}" target="_blank">#{sha}</a> fue creado a través de un 
            Pull Request aceptado, pero no por el método "Merge pull request"<strong></p>
            
            <p>Por políticas de Seguridad Informática se requiere que los Pull Requests sean aceptados a través del 
            método "Merge pull request". Esto se debe a que a través del mismo se mantiene la verificación por clave 
            GPG de los commits resultantes.</p>
            
            <p>El siguiente tutorial indica cómo aplicar esta política a través de branches protegidas en GitHub:
            <a href="https://github.com/despegar/test-signed-commits#ahora-c%C3%B3mo-lo-uso" target="_blank">github.com/despegar/test-signed-commits#aplicación</a></p>
        """.format(sha=commit_sha, url=commit_url)

        self.smtp_connector.send_email(to=[to],
                                       subject='Sobre tu PR aceptado #{sha} en {repo}'.format(sha=commit_sha, repo=repo_name),
                                       message=message)
