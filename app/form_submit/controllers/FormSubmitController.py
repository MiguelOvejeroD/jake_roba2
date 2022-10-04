import json

from flask import request, Blueprint
from commons.controllers.FlaskController import FlaskController
from form_submit.services.FormSubmitService import FormSubmitService

form_submit = Blueprint('form_submit', __name__)

@FlaskController.flask.route("/v3/github/hooks/projects/form-submit", methods=['POST'])
def project_submited():
    fsc = FormSubmitController()
    return fsc.submitProject()

class FormSubmitController():

    def __init__(self):
        self.app = FlaskController.app
        self.form_submit_service = FormSubmitService(self.app)

    def submitProject(self):
        self.app.logger.debug("start request: form submitted")
        response = json.loads(request.form['payload'])
        project_url = ""
        for i in range(0, len(response)):
            response[i] = response[i].split('|')
            if (response[i][0] == "URL del repositorio en github"):
                project_url = response[i][1]
            if (response[i][0] == "Respondant"):
                respondant = response[i][1]
        self.form_submit_service.mark_project_as_submitted(project_url)
        self.form_submit_service.send_appsec_email(response, respondant)
        return "OK", 200
