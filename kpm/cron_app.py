import os
import random
import string
import time

import uvicorn
from fastapi import Depends, FastAPI
from starlette.requests import Request

from kpm.assets.adapters.mongo.views_asset_release import \
    users_with_incoming_releases
from kpm.settings import settings as s
from kpm.shared.adapters.mongo import mongo_client
from kpm.shared.adapters.notifications import EmailNotifications, \
    PushNotifications
from kpm.shared.domain.model import RootAggState
from kpm.shared.domain.time_utils import now_utc_millis
from kpm.shared.entrypoints.fastapi.dependencies import asset_rel_view, \
    asset_view, message_bus
from kpm.shared.entrypoints.fastapi.tasks import repeat_every
from kpm.shared.entrypoints.fastapi.v1 import common_endpoints
from kpm.shared.log import logger
from kpm.users.service_layer.user_handler import _load_email_templates

from kpm.assets.entrypoints.fastapi.dependencies import uows as a_uows
from kpm.users.entrypoints.fastapi.dependencies import uows as u_uows

description = """
## Keepem Cron 

Executes the required backoffice crons to send notifications and so.
"""

version = "0.1"
if os.name != "nt":
    import git

    try:
        repo = git.Repo(search_parent_directories=True)
        version = repo.git.rev_parse(repo.head, short=True)
    except Exception:
        pass

app = FastAPI(
    title=f"{s.APPLICATION_NAME} {s.APPLICATION_COMPONENT}",
    description=description,
    version=version,
)

app.include_router(common_endpoints.router)


app.logger = logger


@app.on_event("startup")
async def startup_event():
    if s.MONGODB_URL:
        with mongo_client() as client:
            logger.info("Creating mongo indexes", component="mongodb")
            assets_db = client["assets"]
            assets_db.assets.create_index("owners_id")
            assets_db.releases.create_index("owner")
            assets_db.releases.create_index("receiver")
            users_db = client["users"]
            users_db.users.create_index("referral_code")
            users_db.keeps.create_index("requester")
            users_db.keeps.create_index("requested")

    logger.info("Application started", component="cron")


@app.on_event("startup")
@repeat_every(seconds=s.CRON_FEEDBACK_EMAIL)
async def cron_feedback():
    logger.info("Cron for feedback email started", component="cron")
    # TODO send email with new keep requests and legacy op
    if not s.EMAIL_SENDER_ADDRESS or not s.EMAIL_SENDER_PASSWORD:
        logger.warning(
            "Can't send notification since no email is set.", component="cron"
        )
        return
    if not s.MONGODB_URL:
        logger.warning(
            "Can't send notification since database is not mongo.",
            component="cron",
        )
        return

    email_notifications = EmailNotifications()
    emails = []
    env = _load_email_templates()
    since = now_utc_millis() - s.CRON_FEEDBACK_EMAIL * 1000

    with mongo_client() as client:
        feedback = client.users.feedback_response
        responses = [
            {
                "form": r["form_id"],
                "question": r["question_id"],
                "response": r["response"],
            }
            for r in feedback.find({"created_ts": since})
        ]
        if responses:
            template = env.get_template("feedback.html")
            body = template.render(responses=responses)
            emails.append(
                {
                    "to": "board@keepem.app",
                    "subject": "Feedback forms",
                    "body": body,
                }
            )
    if emails:
        email_notifications.send_multiple(emails)


@app.on_event("startup")
@repeat_every(seconds=s.CRON_LEGACY)
async def cron_legacy():
    logger.info("Cron for legacy emails started", component="cron")
    if not s.EMAIL_SENDER_ADDRESS or not s.EMAIL_SENDER_PASSWORD:
        logger.warning(
            "Can't send notification since no email is set.", component="cron"
        )
        return
    if not s.MONGODB_URL:
        logger.warning(
            "Can't send notification since database is not mongo.",
            component="cron",
        )
        return

    email_notifications = EmailNotifications()
    emails = []
    env = _load_email_templates()
    since = now_utc_millis() - s.CRON_LEGACY * 1000

    bus = next(message_bus(None, a_uows(), u_uows()))
    users_to_alert = users_with_incoming_releases(since, bus=bus)
    users_batch = [id for id in users_to_alert.keys()]
    logger.info(f"Users to send alerts to {users_batch}")

    with mongo_client() as client:
        emails_cursor = client.users.users.aggregate(
            [
                {"$match": {"_id": {"$in": users_batch}}},
                {"$project": {"_id": 0, "id": "$_id", "email": 1}},
            ]
        )
        for user in emails_cursor:
            logger.debug(f"Sending new legacy email to user {user['id']}")
            template = env.get_template("new_legacy.html")
            founder_name = random.choice(["Martí", "David", "Jordi"])
            body = template.render(founder_name=founder_name)
            emails.append(
                {
                    "to": user["email"],
                    "subject": "New legacy available",
                    "body": body,
                }
            )

    if emails:
        email_notifications.send_multiple(emails)


@app.on_event("startup")
@repeat_every(seconds=s.CRON_PUSH)
async def cron_push_legacy():
    if not s.FIREBASE_CREDENTIALS_FILE:
        logger.warning("Firebase credentials file not set",
                       component="cron")
        return
    logger.info("Cron for push messages started", component="cron")
    if not s.MONGODB_URL:
        logger.warning(
            "Can't send notification since database is not mongo.",
            component="cron",
        )
        return

    messages = []

    bus = next(message_bus(None, a_uows(), u_uows()))
    since = now_utc_millis() - s.CRON_LEGACY * 1000
    users_to_alert = users_with_incoming_releases(since, bus=bus)
    users_batch = [id for id in users_to_alert.keys()]
    logger.debug(f"Users to send alerts to {users_batch}", component="cron")

    logger.info(
        {"messgae": "Number of push messages", "value": len(users_batch)},
        component="cron")

    with mongo_client() as client:
        sessions_cursor = client.users.sessions.aggregate(
            [
                {"$match": {
                    "user": {"$in": users_batch},
                    "state": RootAggState.ACTIVE.value,
                }},
                {"$project": {"_id": 0, "client_id": 1}},
            ]
        )
        for session in sessions_cursor:
            logger.debug(f"Sending new legacy push to client {session['client_id']}")
            messages.append(
                {
                    "client_id": session["client_id"],
                    "subject": "New legacy available",
                }
            )

    if messages:
        notification_svc = PushNotifications()
        notification_svc.send_multiple(messages)
        del notification_svc


@app.on_event("shutdown")
def shutdown_event():
    logger.warning("Application shutdown", component="cron")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    start_time = time.time()
    response = await call_next(request)
    status_code = response.status_code

    process_time_ms = (time.time() - start_time) * 1000
    formatted_process_time = round(process_time_ms, 2)
    logger.info(
        {
            "rid": idem,
            "path": request.url.path,
            "from_ip": request.client.host,  # use --forwarded-allow-ips *
            "method": request.method,
            "elapsed_ms": formatted_process_time,
            "status_code": status_code,
        },
        component="cron",
    )

    return response


if __name__ == "__main__":
    # Debug
    uvicorn.run(app, host="localhost", port=8001, access_log=False)
