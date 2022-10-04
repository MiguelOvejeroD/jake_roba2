"""Generic linux daemon base class for python 3.x."""

import atexit
import os
import signal
import sys
import time
import json

from commons import Application
from commons.controllers.FlaskController import FlaskController

from atpFlask.atp_flask import register_code_url

from project_event.controllers.ProjectEventController import repo_event
from form_submit.controllers.FormSubmitController import form_submit
from push_event.controllers.PushEventController import push_event
from github_to_ldap.controllers.Github2LdapController import github_to_ldap
from organization_event.controllers.OrganizationEventController import org_event

class Daemon:
    """A generic daemon class.

    Usage: subclass the daemon class and override the run() method."""

    def __init__(self, pidfile):
        self.pidfile = pidfile
        self.app = Application()

    def daemonize(self):
        """Deamonize class. UNIX double fork mechanism."""

        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir('/home/despegar/app')
        os.setsid()
        os.umask(0)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write(pid + '\n')

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon."""

        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:

                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = "pidfile {0} already exist. " + \
                      "Daemon already running?\n"
            sys.stderr.write(message.format(self.pidfile))
            sys.exit(1)
        # Start the daemon
        if self.app.context == "prod":
            self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon."""

        # Get the pid from the pidfile
        try:
            print(self.pidfile)
            with open("app/"+self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = "pidfile {0} does not exist. " + \
                      "Daemon not running?\n"
            sys.stderr.write(message.format(self.pidfile))
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err.args))
                sys.exit(1)

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def run(self):
        #register blueprints
        FlaskController.flask.register_blueprint(repo_event)
        FlaskController.flask.register_blueprint(form_submit)
        FlaskController.flask.register_blueprint(push_event)
        FlaskController.flask.register_blueprint(github_to_ldap)
        FlaskController.flask.register_blueprint(org_event)
        #==============

        FlaskController.app = self.app
        host = self.app.config["host"]["host"]
        FlaskController.app.logger.debug("connecting to %s" % host)

        vault_key = FlaskController.app.config.get("atp", "vault_credentials_key")
        atp3_credentials = json.loads(FlaskController.app.config.get("vault", vault_key))
        FlaskController.flask.config.from_mapping(atp3_credentials)
        register_code_url(FlaskController.flask, '/jake/code', '/')

        FlaskController.flask.run(port=9290, host=host)

def main():
    pidfile = "pidfile.pid"
    if (len(sys.argv) == 2):
        daemon = Daemon(pidfile)
        return getattr(daemon, sys.argv[1])()
    else:
        print("expecting argument start|stop|restart")

if __name__ == "__main__":
    main()
