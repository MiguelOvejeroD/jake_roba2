from flask import json
import requests


class SlackConnector:

    def __init__(self, app):
        which_token = app.config.get("slack", "token")
        token = json.loads(app.config.get("vault", which_token))['key']
        self.url = app.config.get("slack", "url") + token

    def send_message(self, channel, message, username="Jake"):
        payload = {}
        payload["channel"] = channel
        payload["username"] = username
        payload["text"] = message
        payload_json = json.dumps(payload)
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        return requests.post(self.url, data=payload_json, headers=headers)

    def send_attachment(self, channel, message="", fallback="", username="Jake", title="", text="", color="#439FE0", pretext=""):
        payload = {
            "channel": channel,
            "message": message,
            "attachments": [
                {
                    "fallback": fallback,
                    "color": color,
                    "pretext": pretext,
                    "author_name": username,
                    "title": title,
                    "text": text
                }
            ]
        }
        headers = {'content-type': 'application/json'}
        return requests.post(self.url, data=str(payload), headers=headers)
