import os
import random
import string
import time
from os.path import dirname, join

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request

from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.settings import settings as s
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
* Stash an asset somewhere to be recovered in the future 🌍
* Send it away inside a bottle 🧴🏖️
* Give it to someone 🤝

"""

version = "0.1"
if os.name != "nt":
    import git

    try:
        repo = git.Repo(search_parent_directories=True)
        version = repo.git.rev_parse(repo.head, short=True)
    except:
        pass

app = FastAPI(
    title=s.APPLICATION_NAME,
    description=description,
    version=version,
)

app.include_router(users_router)
app.include_router(assets_router)


app.logger = logger


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")


@app.on_event("shutdown")
def shutdown_event():
    logger.warn("Application shutdown")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(
        '{"rid":"%s", "from": "%s", "method":"%s", "path": "%s"}',
        idem,
        f"{request.client.host}:{request.client.port}",
        request.method,
        request.url.path,
    )
    start_time = time.time()
    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    logger.info(
        '{"rid":"%s", "completed_in":"%sms", "status_code":"%s"}',
        idem,
        formatted_process_time,
        response.status_code,
    )

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
