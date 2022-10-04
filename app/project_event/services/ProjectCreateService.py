import re
from collections import OrderedDict
from datetime import datetime
from commons.connectors.SMTPConnector import SMTPConnector
from commons.connectors.LDAPConnector import LDAPConnector
from commons.connectors.GoogleSheetsConnector import GoogleSheetsConnector, ResultMode


class ProjectCreateService:

    def __init__(self, app):
        self.logger = app.logger
        self.config = app.config
        self.smtp_connector = SMTPConnector(app)
        self.ldap_connector = LDAPConnector(app)
        self.google_sheets_connector = GoogleSheetsConnector(app)

    def send_email_to(self, to, url):
        self.logger.debug("sending email")

        message = """
        <p>Se detectó recientemente la creación de un nuevo repositorio en Github.</p>
        <p>"""+url+"""</p> 
        <p>Por favor, complete la siguiente encuesta de seguridad para ayudarnos: </p>
        """+self.config.get('forms', 'link')+'&entry.1419592804='+url

        appsec_message = """
        <p>El usuario """+to+""" creo el repositorio """+url+""".</p> 
        <p>link a sheet: """+self.config.get('workbook', 'sheet_url')+"""</p>"""

        self.smtp_connector.send_email(to=[to],
                                                 subject='Encuesta de seguridad',
                                                 message=message)
        #self.smtp_connector.send_email(to=[self.config.get('appsec', 'email')],
        #                                         subject='nuevo repo creado',
        #                                         message=appsec_message)

    def get_ldap_user(self, user):
        attr = re.split(";|,", self.config.get("ldap", "query.attributes"))
        attributes = list(OrderedDict.fromkeys(attr).keys())
        value = self.ldap_connector.find("(userPrincipalName="+user+")", attributes=attributes)
        return value

    def project_created(self, project_name, project_url, status, submitted, email):
        self.logger.debug("inserting google sheet row")
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [[project_url, project_name, status, email, submitted, date, ""]]
        try:
            self.google_sheets_connector.single_row(self.config.get("workbook", "spreadsheet_id"), self.config.get('sheet', 'sheet.id'), values, "append")
        except Exception as e:
            self.logger.error("failed to insert gsheet row: %s" % str(e))
            self.logger.error("project: %s - %s - %s" % (project_name, project_url, email))
            self.send_error_email(project_name, project_url, email, date)

    def project_modified(self, project_url, status):
        sheet = self.google_sheets_connector.single_range_fetch(self.config.get("workbook", "spreadsheet_id"),
                                                                the_range="submitted_forms", result_mode=ResultMode.RAW)
        for i in range(1, len(sheet)):
            if (sheet[i][0] == project_url):
                row = i + 1
                # set ranges
                ran = "!A" + str(row) + ":G" + str(row)
                # udpdate row
                sheet[i][2] = status
                #status = S --- suspendido|stand by,
                # el proyecto se cerró, y hasta que no se vuelva a abrir no se reenvía el email
                #solo si no completó el formulario previamente
                if (status == "closed" and sheet[i][4] != "V"):
                    sheet[i][4] = "S"
                elif (status == "reopened" and sheet[i][4] != "V"):
                    sheet[i][4] = "F"
                # reinsert row
                self.google_sheets_connector.single_row(self.config.get("workbook", "spreadsheet_id"),
                                                               "submitted_forms" + ran, [sheet[i]], "update")
                self.logger.info("update row for project %s" % project_url)
                break
        return 'ok', 200

    def project_deleted(self, url):
        sheet = self.google_sheets_connector.single_range_fetch(self.config.get("workbook", "spreadsheet_id"),
                                                                the_range="submitted_forms", result_mode=ResultMode.RAW)
        for i in range(1, len(sheet)):
            if ((len(sheet[i]) > 0) and (sheet[i][0] == url)):
                if (i < len(sheet)):
                    for j in range(i, len(sheet) - 1):
                        sheet[j] = sheet[j + 1]
                        if (len(sheet[j]) < 7):
                            sheet[j].append("")
                ran = "!A" + str(i + 1) + ":G" + str(len(sheet))
                sheet[len(sheet) - 1] = [""] * 7
                final_sheet = sheet[i:len(sheet)]
                self.google_sheets_connector.write2(self.config.get("workbook", "spreadsheet_id"), "submitted_forms" + ran, final_sheet)
                break
        return 'ok', 200

    def send_error_email(self, project_name, project_url, email, date):
        self.logger.debug("sending error email")
        message = """
        <p>Falló la inserción de un repositorio creado en github</p>
        
        <p>repositorio: """+project_name+"""</p>
        <p>url: """+project_url+"""</p>
        <p>creador: """+email+"""</p>
        <p>fecha: """+date+"""</p>
        
        <p>revisar los logs para mas información</p>
        """
        self.smtp_connector.send_with_attachment(to=[self.config.get('appsec', 'email')],
                                                 subject='Fallo la inserción de una entrada en la lista de repositorios',
                                                 message=message)
