import base64
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from timeit import default_timer as timer
from typing import List, Union

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
        self, host: str = s.EMAIL_SMTP_SERVER, port: int = s.EMAIL_SMTP_PORT
    ):
        start = timer()
        self.server = smtplib.SMTP(host, port)
        self.server.noop()
        print("smtp setup took (%.2f seconds passed)" % (timer() - start,))
        self.__pwd = str(
            base64.b64decode(s.EMAIL_SENDER_PASSWORD), "utf-8"
        ).replace("\n", "")

    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        start = timer()

        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = s.EMAIL_SENDER_ADDRESS
        message["To"] = destination
        message.attach(MIMEText(body, "html"))
        msg_body = message.as_string()

        self.server.starttls()
        print(
            "starttls started took (%.2f seconds passed)" % (timer() - start,)
        )

        self.server.login(s.EMAIL_SENDER_ADDRESS, self.__pwd)

        print("login took (%.2f seconds passed)" % (timer() - start,))
        self.server.sendmail(s.EMAIL_SENDER_ADDRESS, destination, msg_body)
        print("sending took (%.2f seconds passed)" % (timer() - start,))

        logger.info(f"Email sent to '{destination}' with subject '{subject}'")


class NoNotifications(AbstractNotifications):
    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        logger.info(
            "I would have send email to "
            + f"'{destination}' with subject '{subject}'"
        )
