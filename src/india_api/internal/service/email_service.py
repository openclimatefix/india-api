import os

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
from fastapi import BackgroundTasks

load_dotenv(".env")

def generate_csv_data():
    from india_api.internal.service.server import generate_csv_data
    return generate_csv_data()

class Envs:
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_FROM = os.getenv("MAIL_FROM")
    MAIL_PORT = int(os.getenv("MAIL_PORT"))
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_FROM_NAME = os.getenv("MAIN_FROM_NAME")


conf = ConnectionConfig(
    MAIL_USERNAME=Envs.MAIL_USERNAME,
    MAIL_PASSWORD=Envs.MAIL_PASSWORD,
    MAIL_FROM=Envs.MAIL_FROM,
    MAIL_PORT=Envs.MAIL_PORT,
    MAIL_SERVER=Envs.MAIL_SERVER,
    MAIL_FROM_NAME=Envs.MAIL_FROM_NAME,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER="../templates/email",
)


async def send_email_async(subject: str, email_to: str, body: dict, attachment=None):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html",
    )

    if attachment:
        message.attachment = attachment

    fm = FastMail(conf)
    await fm.send_message(message, template_name="email.html", app=server)


# not used in the current implementation, but it could be useful if we want to offload the
# email sending task to a background process, allowing the API to respond more quickly to the client.
def send_email_background(
    background_tasks: BackgroundTasks,
    subject: str,
    email_to: str,
    body: dict,
    attachment=None,
):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html",
    )

    if attachment:
        message.attachment = attachment

    fm = FastMail(conf)
    background_tasks.add_task(
        fm.send_message, message, template_name="email.html", app=server
    )
