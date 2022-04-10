import base64
import smtplib
import traceback
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Union
from fastapi import BackgroundTasks

from kpm.settings import settings as s
from kpm.shared.log import logger


class AbstractNotifications(ABC):
    @abstractmethod
    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        raise NotImplementedError


class EmailNotifications(AbstractNotifications):
    """
    NOTE: this takes 30s just to init.
    """

    def __init__(
        self, background_tasks: BackgroundTasks = None,
            host: str = s.EMAIL_SMTP_SERVER, port: int = s.EMAIL_SMTP_PORT
    ):
        self._host = host
        self._port = port
        self._bg_tasks = background_tasks

    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = f"Keepem App <{s.EMAIL_SENDER_ADDRESS}>"
        message["Reply-To"] = "Keepem Info <info@keepem.app>"
        message["To"] = destination
        message.attach(MIMEText(body, "html"))
        msg_body = message.as_string()

        if self._bg_tasks:
            self._bg_tasks.add_task(
                EmailNotifications._connect_and_send,
                self._host, self._port, destination, msg_body
            )
        else:
            logger.warning("Synchronously sending email", component="mail")
            EmailNotifications._connect_and_send(self._host, self._port,
                                                 destination, msg_body)

        logger.info(
            f"Email sent to '{destination}' with subject '{subject}'",
            component="mail",
        )

    @staticmethod
    def _connect_and_send(host, port, destination, msg_body):
        try:
            server = smtplib.SMTP(host, port)
            server.noop()
            server.starttls()
            pwd = str(
                base64.b64decode(s.EMAIL_SENDER_PASSWORD), "utf-8"
            ).replace("\n", "")
            server.login(s.EMAIL_SENDER_ADDRESS, pwd)
            server.sendmail(s.EMAIL_SENDER_ADDRESS, destination, msg_body)
            server.close()
        except Exception as e:
            logger.error({
                "message": str(e),
                "stack": str(traceback.format_exc())[-168:]}
                , component='mail'
            )
            raise e


class NoNotifications(AbstractNotifications):
    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        logger.info(
            "I would have send email to "
            + f"'{destination}' with subject '{subject}'",
            component="notifications",
        )
