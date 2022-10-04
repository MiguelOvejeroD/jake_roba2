from ldap3 import Tls, Server, Connection, ALL
import ssl
import json


def values_in_order(d, attributes):
    return [d[a] for a in attributes] # dict.values() has random order


class LDAPConnector:

    def __init__(self, app):
        self.logger = app.logger
        self.tls_configuration = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1)
        self.server = Server(app.config.get("ldap", "ldap.server"),
                             get_info=ALL, use_ssl=True, tls=self.tls_configuration)
        which_credentials = app.config.get("ldap", "vault_credentials_key")
        credentials = json.loads(app.config.get("vault", which_credentials))
        self.logger.debug("Connecting to LDAP (%s)" % app.config.get("ldap", "ldap.server"))
        self.conn = Connection(self.server, credentials["user"], credentials["pass"], auto_bind=True)

        self.search_base = app.config.get("ldap", "search_base")
        self.attributes = app.config.get("ldap", "query.attributes").split(",")

    def find(self, query, search_base=None, attributes=None):
        self.conn.search(search_base=search_base or self.search_base,
                         search_filter=query,
                         attributes=attributes or self.attributes)
        # self.logger.debug("LDAP entries: %s", self.conn.entries)
        values = [entry.entry_attributes_as_dict for entry in self.conn.entries]

        result = []
        for val in values:
            t = []
            for attr_val in values_in_order(val, attributes or self.attributes):
                if len(attr_val) > 0:
                    t.append(str(attr_val[0]))
                else:
                    t.append('')
            result.append(tuple(t))
        return result
