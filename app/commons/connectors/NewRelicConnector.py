__author__ = 'inieto'

import newrelic.agent
import sys
import http.client
import json
from urllib import parse


class NewRelicConnector:

    def __init__(self, app):
        self.logger = app.logger
        self.config = app.config
        self.group = "BackgroundJobs"
        self.application = None
        self.initialize_newrelic()

        which_credentials = app.config.get("newrelic", "vault_credentials_key")
        credentials = json.loads(app.config.get("vault", which_credentials))
        self.headers = {"Accept": "application/json", "X-Query-Key": credentials["key"]}
        self.conn = http.client.HTTPSConnection(app.config.get("newrelic", "insights.host"), 443)

    def initialize_newrelic(self):
        conf_file = self.config.get("newrelic", "config_file")
        newrelic.agent.initialize(conf_file)
        self.application = newrelic.agent.register_application(timeout=10.0)

    def record_metric(self, task_name, custom_metric_name, custom_metric_value, atributes):
        self.logger.debug(" Setting transaction name")
        newrelic.agent.set_transaction_name(task_name, self.group)

        # attributes or facets
        self.logger.debug(" adding custom parameters")
        for name, value in atributes.items():
            newrelic.agent.add_custom_parameter(name.replace(" ", "_"), value)

        self.logger.debug(" recording custom metric")
        newrelic.agent.record_custom_metric('Custom/'+custom_metric_name, custom_metric_value)

        self.logger.debug(" ending transaction")
        newrelic.agent.end_of_transaction()

    def record_event(self, task_name, custom_event_name, attributes):
        self.logger.debug(" Setting transaction name")
        newrelic.agent.set_transaction_name(task_name, self.group)

        # attributes or facets
        self.logger.debug(" adding custom parameters")
        for name, value in attributes.items():
            newrelic.agent.add_custom_parameter(name.replace(" ", "_"), value)

        self.logger.debug(" recording custom event")
        newrelic.agent.record_custom_event('Custom/'+custom_event_name, attributes)

        self.logger.debug(" ending transaction")
        newrelic.agent.end_of_transaction()

    def record_exception(self, message, params):
        try:
            raise Exception()
        except Exception as exc:
            newrelic.agent.record_exception(params=params, application=self.application,
                                            exc=exc, value=message, tb=sys.exc_info()[2])

    def execute_insights_query(self, query):
        self.conn.request(method="GET", headers=self.headers,
                          url=self.config.get("newrelic", "insights.path") + "?nrql=" + parse.quote_plus(query))
        resp = self.conn.getresponse()
        self.logger.debug("Insights Query Response: (%s, %s)" % (resp.status, resp.reason))
        resp_json = json.loads(resp.read().decode("utf-8"))
        return resp_json
