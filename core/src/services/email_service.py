from sendgrid import Mail
from etc import settings


class EmailServiceImpl:
    def __init__(self, sendgrid):
        self.sendgrid = sendgrid

    @staticmethod
    def _get_html_template(template_name, context):
        templates = {
            'confirm_email': '<a href="{confirm_link}">Click here to confirm email</a>'
        }
        return templates[template_name].format(**context)

    def send_email_address_confirmation(self, email_address, email_token):
        ctx = {
            'confirm_link': '{}://{}:{}/auth/confirm_email/{}'.format(
                settings.WEB_PROTOCOL,
                settings.WEB_HOSTNAME,
                settings.WEB_PORT,
                email_token
            )
        }
        message = Mail(
            from_email='guido.dassori@gmail.com',
            to_emails=email_address,
            subject='Would you please confirm your email address',
            html_content=self._get_html_template('confirm_email', ctx))
        response = self.sendgrid.send(message)
        return response
