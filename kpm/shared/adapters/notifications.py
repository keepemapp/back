import base64
import smtplib
import traceback
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Union

from fastapi import BackgroundTasks

from kpm.settings import settings as s
from kpm.shared.log import logger


class AbstractNotifications(ABC):
    @abstractmethod
    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        raise NotImplementedError

    @abstractmethod
    def send_multiple(self, emails: List[Dict]):
        raise NotImplementedError


class EmailNotifications(AbstractNotifications):
    """
    NOTE: sending is slow
    """

    def __init__(
        self,
        background_tasks: BackgroundTasks = None,
        host: str = s.EMAIL_SMTP_SERVER,
        port: int = s.EMAIL_SMTP_PORT,
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
            logger.debug(
                f"Sending email to '{destination}'",
                component="mail",
            )
            self._bg_tasks.add_task(
                EmailNotifications._connect_and_send,
                self._host,
                self._port,
                destination,
                msg_body,
                subject,
            )
        else:
            logger.warning("Synchronously sending email", component="mail")
            EmailNotifications._connect_and_send(
                self._host, self._port, destination, msg_body, subject
            )

    def send_multiple(self, emails: List[Dict]):
        msgs = []
        for email in emails:
            message = MIMEMultipart()
            message["Subject"] = email["subject"]
            message["From"] = f"Keepem App <{s.EMAIL_SENDER_ADDRESS}>"
            message["Reply-To"] = "Keepem Info <info@keepem.app>"
            message["To"] = email["to"]
            message.attach(MIMEText(email["body"], "html"))
            msgs.append(message)
        if self._bg_tasks:
            self._bg_tasks.add_task(
                EmailNotifications._send_multiple, self._host, self._port, msgs
            )
        else:
            logger.warning("Synchronously sending email", component="mail")
            EmailNotifications._send_multiple(self._host, self._port, msgs)

    @staticmethod
    def _connect_and_send(host, port, destination, msg_body, subject):
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
            logger.info(
                f"Email sent to '{destination}' with subject '{subject}'",
                component="mail",
            )
        except Exception as e:
            logger.error(
                {
                    "message": str(e),
                    "stack": str(traceback.format_exc())[-168:],
                },
                component="mail",
            )

    @staticmethod
    def _send_multiple(host, port, messages: List[MIMEMultipart]):
        try:
            server = smtplib.SMTP(host, port)
            server.noop()
            server.starttls()
            pwd = str(
                base64.b64decode(s.EMAIL_SENDER_PASSWORD), "utf-8"
            ).replace("\n", "")
            server.login(s.EMAIL_SENDER_ADDRESS, pwd)
            for msg in messages:
                try:
                    msg_body = msg.as_string()
                    server.sendmail(
                        s.EMAIL_SENDER_ADDRESS, msg["To"], msg_body
                    )
                    logger.info(
                        f"Email sent to '{msg['To']}' with subject '{msg['Subject']}'",
                        component="mail",
                    )
                except Exception as e:
                    logger.error(
                        {
                            "message": str(e),
                            "stack": str(traceback.format_exc())[-168:],
                        },
                        component="mail",
                    )
            server.close()
        except Exception as e:
            logger.error(
                {
                    "message": str(e),
                    "stack": str(traceback.format_exc())[-168:],
                },
                component="mail",
            )


class NoNotifications(AbstractNotifications):
    def send(
        self, destination: Union[List[str], str], subject: str, body: str
    ):
        logger.info(
            "I would have send email to "
            + f"'{destination}' with subject '{subject}'",
            component="notifications",
        )

    def send_multiple(self, emails: List[Dict]):
        logger.info(
            f"I would have send {emails} ",
            component="notifications",
        )
