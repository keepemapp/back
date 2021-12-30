import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Union

from kpm.settings import settings as s

logger = logging.getLogger("kpm")


class AbstractNotifications(ABC):
    @abstractmethod
    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        raise NotImplementedError


class EmailNotifications(AbstractNotifications):
    def __init__(
        self, host: str = s.EMAIL_SMTP_SERVER, port: int = s.EMAIL_SMTP_PORT
    ):
        self.server = smtplib.SMTP(host, port)
        self.server.noop()

    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):

        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = s.EMAIL_SENDER_ADDRESS
        message["To"] = destination
        message.attach(MIMEText(body, "html"))
        msg_body = message.as_string()

        self.server.starttls()
        logging.info(
            f"Sending email to '{destination}' with subject '{subject}'"
        )
        self.server.login(s.EMAIL_SENDER_ADDRESS, s.EMAIL_SENDER_PASSWORD)
        self.server.sendmail(s.EMAIL_SENDER_ADDRESS, destination, msg_body)


class NoNotifications(AbstractNotifications):
    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        logging.info(
            "I would have send email to "
            + f"'{destination}' with subject '{subject}'"
        )
