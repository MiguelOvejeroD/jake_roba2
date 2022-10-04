from collections import OrderedDict
import re
from commons.connectors.LDAPConnector import LDAPConnector
from commons.connectors.SMTPConnector import SMTPConnector


class OrganizationEventService():

    def __init__(self, app):
        self.logger = app.logger
        self.config = app.config
        self.ldap_connector = LDAPConnector(app)
        self.smtp_connector = SMTPConnector(app)

    def get_ldap_user(self, user):
        attr = re.split(";|,", self.config.get("ldap", "query.attributes"))
        attributes = list(OrderedDict.fromkeys(attr).keys())
        value = self.ldap_connector.find("(userPrincipalName="+user+")", attributes=attributes)
        return value

    def send_user_email(self, email, usuario):
        message = """
        <p>Buenos días</p>
        <p>Recientemente se agrego al usuario <b>"""+usuario+"""</b> a la organizacion "Despegar" en github</p>
        </br>
        <p>Por favor, asociá tu usuario al backoffice de Despegar en http://backoffice.despegar.com/github</p>
        """
        self.smtp_connector.send_email(to=[email],
                                        subject='Asociacion de usuario de github a backoffice de Despegar',
                                        message=message)

    def send_sender_email(self, email, usuario):
        message = """
        <p>Buenos días</p>
        <p>Notamos que agregaste al usuario <b>""" + usuario + """</b> a la organizacion "Despegar" en github</p>
        </br>
        <p>Por favor, requerimos que el mismo se asocie a su usuario de ATP en http://backoffice.despegar.com/github</p>
        """
        self.smtp_connector.send_email(to=[email],
                                       subject='Asociacion de usuario de github a backoffice',
                                       message=message)

    def send_appsec_email(self, usuario, sender):
        message = """
                <p>El usuario <b>"""+sender+"""</b> agrego recientemente al usuario <b>""" + usuario + """</b> a la organizacion "Despegar" en github</p>
                </br>
                <p>No se encontro usuario de ATP para ninguno de los dos</p>
                """
        self.smtp_connector.send_email(to=[self.config.get('appsec', 'email')],
                                       subject='Asociacion de usuario de github a backoffice',
                                       message=message)


