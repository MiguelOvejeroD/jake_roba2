from datetime import datetime
from commons.connectors.GoogleSheetsConnector import GoogleSheetsConnector, ResultMode
from commons.connectors.SMTPConnector import SMTPConnector

class FormSubmitService:
    def __init__(self, app):
        self.infoIndex = ["Tarjetas de Crédito", "Emails", "Nombre y Apellido", "Documentos", "Direcciones", "Teléfonos", "Cupones de Descuento", "KPIs"]
        self.logger = app.logger
        self.config = app.config
        self.google_sheets_connector = GoogleSheetsConnector(app)
        self.smtp_connector = SMTPConnector(app)

    def mark_project_as_submitted(self, project_url):
        sheet = self.google_sheets_connector.single_range_fetch(self.config.get("workbook", "spreadsheet_id"), the_range="submitted_forms", result_mode=ResultMode.RAW)
        try:
            for i in range(1, len(sheet)):
               if (sheet[i][0] == project_url):
                   row = i+1
                   #set ranges
                   ran = "!A"+str(row)+":G"+str(row)
                   #udpdate row
                   sheet[i][4] = 'V'
                   if (len(sheet[i]) == 7):
                       sheet[i][6] = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                   else:
                       sheet[i] += [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

                   #reinsert row
                   self.google_sheets_connector.single_row(self.config.get("workbook", "spreadsheet_id"), "submitted_forms"+str(ran), [sheet[i]], "update")
                   self.logger.info("update row for project %s" % project_url)
                   break
            return "ok", 200
        except Exception as e:
            self.logger.error("failed to update gsheet row: %s" % str(e))
            self.logger.error("project: %s" % project_url)
            raise e


    def send_appsec_email(self, responses=None, respondant=None):
        self.logger.debug("sending email to appsec")
        message = """
        <p>Hola!</p>
<p>Gracias por responder la encuesta de seguridad!</p>

<p>Si necesitan una mano con la arquitectura de la aplicación, podemos ayudar para tratar los temas de seguridad desde el inicio. </p>

<p>En principio, nosotros desarrollamos una herramienta llamada Dupin (https://github.com/despegar/dupin) para la encripción o tokenización de datos los sensibles de los pasajeros (Emails, Nombre y apellido, Documentos, Direcciones, Teléfonos, Cupones de Descuento e Indicadores clave confidenciales de la compañía) similar a DVault para la encripción de los datos de la Tarjeta de Crédito.</p>

<p>Estamos promoviendo el uso de la misma, y sería éste el caso dado las respuestas que nos indicaste en el formulario.</p>
<p>Podés responder y hablar con nosotros a appsec@despegar.com</p>

<p>Muchas gracias!</p>

<p>Tus respuestas:</p>

"""
        mailable = False
        for i in range(0, len(responses)):
            #if (responses[i][0] == "¿La aplicación guardará estado persistente?"):
            #    if ("No, no almacenará datos de ningún tipo" in responses[i][1]):
            #        mailable = False
            #        break
            if(responses[i][0] == '¿Manejará información sensible?'):
                response_string = responses[i][1]
                message += "<br>"+responses[i][0] +"</br>"
                response_array = response_string.split(",")
                for i in range(0, len(response_array)):
                    if ('Si' == response_array[i]):
                        message += "<br>"+self.infoIndex[i]+"</br>"
                #mailable se modifica una sola vez al detectar un dato sensible
                mailable = not mailable and 'Si' in response_string
            else:
                message += "<p>"+responses[i][0] +": "+responses[i][1]+ "</p>"

        if mailable:
            subject = responses[6][1].split("/")[4]
            self.smtp_connector.send_email(to=[self.config.get('appsec', 'email'), respondant],
                                                subject='ATENCION: nuevo repositorio con informacion sensible: '+subject,
                                                 message=message)

    def send_error_email(self, project_url):
        self.logger.debug("sending error email")
        message = """Falló el registro del submit de un formulario para el siguiente repositorio

        url: """ + project_url + """

        revisar los logs para mas información
        """
        self.smtp_connector.send_with_attachment(to=[self.config.get('appsec', 'email')],
                                                 subject='Fallo la actualización de una entrada en la lista de repositorios',
                                                 message=message)
