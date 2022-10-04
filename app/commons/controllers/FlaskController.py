import os
from flask import Flask, request, send_from_directory
import time
import traceback

from commons.connectors.SlackConnector import SlackConnector


class FlaskController:

    template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
    template_dir = os.path.join(template_dir, 'templates')
    flask = Flask(__name__, template_folder=template_dir)
    app = None
    @flask.errorhandler(Exception)
    def handle_exception(e):
        FlaskController.app.logger.error("Exception: " + str(e))
        if (FlaskController.app.context == 'prod'):
            slack_connector = SlackConnector(FlaskController.app)
            split = traceback.format_exc().split("\n")
            split_len = len(split)
            params = {'date': time.strftime("%c"),
                      'path': request.path,
                      'endpoint': request.endpoint,
                      'http_user_agent': request.environ['HTTP_USER_AGENT'],
                      'traceback': split[split_len - 4],
                      'message': split[split_len - 2]}
            message = FlaskController.build_slack_message(params=params)
            slack_connector.send_message('#jake', message=message, username='Jake')
            return 'Internal Server Error', 500

    @staticmethod
    @flask.route("/healthcheck", host="localhost", methods=['POST', 'GET'])
    def healthcheck():
        return "OK", 200

    @staticmethod
    @flask.route('/favicon.ico')
    def favicon():
        return send_from_directory("../assets", 'favicon.ico', mimetype='image/vnd.microsoft.icon')
        #return "ok", 200

    def build_slack_message(params):
        if 'traceback' in params:
            params['traceback'] = '```' + traceback.format_exc() + '```'
        message = ""
        for key, value in params.items():
            if key and value:
                message += "*"+key+"*: "+value+"\n"
        return message

    @staticmethod
    def alert(message, pretext, title="Jake Alert Triggered"):
        FlaskController.app.logger.warning("Alert: " + message)
        slack_connector = SlackConnector(FlaskController.app)
        params = {'Date': time.strftime("%c"),
                  'Alert': message}
        message = FlaskController.build_slack_message(params=params)
        slack_connector.send_attachment(channel='#jake',
                                        pretext=pretext,
                                        text=message,
                                        color="warning",
                                        title=title,
                                        fallback=pretext)

