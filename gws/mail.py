from fastapi_mail import FastMail

from gws.logger import Logger
from gws.settings import Settings



class Email:
    
    @staticmethod
    async def send(to_address, subject, message):
        settings = Settings.retrieve()
        if settings.smtp is None:
            Logger.error("No SMTP configuration found")

        mail = FastMail(
            settings.smtp["login"],
            settings.smtp["login"],
            tls=settings.smtp["tls"]
        )

        await  mail.send_message(to_address, subject, message, text_format="html")
