import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders


class SMTPConnector:

    def __init__(self, app):
        self.logger = app.logger
        self.config = app.config

    """
        [email]
        default_from = {'name': 'App-Sec', 'email': 'app-sec@despegar.com'}
        default_to = ['appsec@despegar.com']
        default_subject = 'Encuesta de seguridad'
    """
    # TODO DEPRECATED
    def send_with_attachment(self, sender=None, to=None, subject=None, message=None, files=None):
        if files is None:
            files = []
        if to is None:
            to = []
        self.send_email(sender, to, subject, message, files)

    """
        Sends an email with the specified sender, subject and message to recipient `to`.
        File attachments can be optionally included, using the `files` parameter.
        
        The `message` parameter is wrapped in an HTML string which includes AppSec's header and footer
        and some additional styling. This means that `message` can (and is strongly encouraged to) be HTML. 
        Additional CSS styling can be applied with the `styles` parameter.
        If you would like to completely omit this HTML wrapping, set `omit_html_wrapping` to True.
        
        To include images in your HTML message, the `img_id_path_tuples` parameter takes a list
        in the form of [(String, String)], where the first part of the tuple is the path to the image file,
        and the second part is an id which references it. In your HTML then reference the img by its id.
        
        Example:
            <img src="cid:header">
            
            img_path_id_tuples=[("path/to/header.png"), 'header')]
        
    """
    def send_email(self, sender=None, to=None, subject=None, message=None, files=None,
                   img_path_id_tuples=None, styles='', omit_html_wrapping=False):
        if to is None:
            to = []
        if files is None:
            files = []
        if img_path_id_tuples is None:
            img_path_id_tuples = []

        sender = sender if sender else json.loads(self.config.get("email", "default_sender"))
        msg = MIMEMultipart()
        msg['From'] = '{server} <{mail}>'.format(server=sender["name"], mail=sender["email"])
        msg['To'] = ", ".join(to if len(to) > 0 else json.loads(self.config.get("email", "default_to")))
        msg['Subject'] = msg.preamble = subject if subject else self.config.get("email", "default_subject")

        html_message = """
            <head>
            <meta charset="UTF-8">
            <style>
                div.content {
                    color: black;
                    font-size: 1rem;
                    width: 700px;
                    padding: 5px 10px;
                }
                """ + styles + """
            </style>
            </head>""" + """
            <body>
            <div class="content">
                <img src="cid:header">
                {content}
                <p>Muchas gracias,<br />
                Application Security @ Despegar</p>
                <img src="cid:footer">
            </div>
            </body>
            """.format(content=message)

        msg.attach(MIMEText(html_message if not omit_html_wrapping else message, 'html'))

        current_path = os.path.dirname(__file__)

        if not omit_html_wrapping:
            header = ("../assets/appsec-mail-header.png", 'header')
            footer = ("../assets/appsec-mail-footer.png", 'footer')
            img_path_id_tuples.append(header)
            img_path_id_tuples.append(footer)

        for img_tuple in img_path_id_tuples:
            img = open(img_tuple[0], 'rb')
            msg_image = MIMEImage(img.read())
            img.close()
            msg_image.add_header('Content-ID', '<{cid}>'.format(cid=img_tuple[1]))
            msg.attach(msg_image)

        for f in files:
            fpart = MIMEBase('application', 'octet-stream')
            with open(f, 'rb') as fp:
                fpart.set_payload(fp.read())
            encoders.encode_base64(fpart)
            fpart.add_header('Content-Disposition', 'attachment', filename=f)
            msg.attach(fpart)

        s = smtplib.SMTP(self.config.get("email", "smtp_server"))
        s.set_debuglevel(1)
        """
         >>> import smtplib
         >>> s=smtplib.SMTP("localhost")
         >>> tolist=["one@one.org","two@two.org","three@three.org","four@four.org"]
         >>> msg = '''\\
         ... From: Me@my.org
         ... Subject: testin'...
         ...
         ... This is a test '''
         >>> s.sendmail("me@my.org",tolist,msg)
        """
        try:
            s.sendmail(sender["email"], to, msg.as_string().encode('UTF-8'))
        except smtplib.SMTPRecipientsRefused as err:
            self.logger.debug("Recipient refused")
            self.logger.debug(err)
        finally:
            s.close()
        print('Sending email...')
