import os
import random
import string
import time

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request

from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.settings import settings as s
from kpm.shared.adapters.mongo import mongo_client
from kpm.shared.entrypoints.fastapi.v1 import common_endpoints
from kpm.shared.log import logger
from kpm.users.entrypoints.fastapi.v1 import users_router

description = """
Keepem API helps you managing your emotional assets and memories 💖

## Users

You can register a new user and log in

## Assets 🖼️📹📄🎵

You can create assets (via 2 part transaction for now)

## Kepp'em moving 💌🏃

You can share your memories in multiple and creative ways: with others or even
yourself!

Try to:
* Send an asset to your future self ✉️🔮
* Create a time capsule ⏳🎁
* Hide an asset somewhere to be recovered in the future 🌍
* Send it away inside a bottle 🧴🏖️
* Give it to someone 🤝

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
    title=s.APPLICATION_NAME,
    description=description,
    version=version,
)

app.include_router(users_router)
app.include_router(assets_router)
app.include_router(common_endpoints.router)


app.logger = logger


@app.on_event("startup")
async def startup_event():
    if s.MONGODB_URL:
        logger.info("Creating mongo indexes")
        with mongo_client() as client:
            assets_db = client["assets"]
            assets_db.assets.create_index("owners_id")
            assets_db.releases.create_index("owner")
            assets_db.releases.create_index("receiver")
            users_db = client["users"]
            users_db.users.create_index("referral_code")
            users_db.keeps.create_index("requester")
            users_db.keeps.create_index("requested")

    logger.info("Application started")


@app.on_event("shutdown")
def shutdown_event():
    logger.warn("Application shutdown")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info({
        "rid": idem,
        "from":  f"{request.client.host}:{request.client.port}",
        "method": request.method,
        "path": request.url.path
    })
    start_time = time.time()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        logger.error(str(e), component="api")

    process_time_ms = (time.time() - start_time) * 1000
    formatted_process_time = round(process_time_ms, 2)
    logger.info({
        "rid": idem,
        "completed_in_ms": formatted_process_time,
        "status_code": status_code
    })

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000, access_log=False)
