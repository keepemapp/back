import logging
import os
import pathlib

import uvicorn
from fastapi import FastAPI

from kpm.assets.infra.fastapi.v1 import assets_router
from kpm.settings import settings as s
from kpm.users.infra.fastapi.v1 import users_router

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

    repo = git.Repo(search_parent_directories=True)
    version = repo.git.rev_parse(repo.head, short=True)

app = FastAPI(
    title=s.APPLICATION_NAME,
    description=description,
    version=version,
)

app.include_router(users_router)
app.include_router(assets_router)


# cwd = pathlib.Path(__file__).parent.resolve()
# logging.config.fileConfig(
#     os.path.join(cwd, "logging.conf"), disable_existing_loggers=False
# )
# logger = logging.getLogger('kpm')
#
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     idem = "".join(
#         random.choices(string.ascii_uppercase + string.digits, k=6)
#     )
#     logger.info(
#         '{"rid":"%s", "method":"%s", "path": "%s"}',
#         idem,
#         request.method,
#         request.url.path,
#     )
#     start_time = time.time()
#
#     response = await call_next(request)
#
#     process_time = (time.time() - start_time) * 1000
#     formatted_process_time = "{0:.2f}".format(process_time)
#     logger.info(
#         '{"rid":"%s", "completed_in":"%sms", "status_code":"%s"}',
#         idem,
#         formatted_process_time,
#         response.status_code,
#     )
#
#     return response

cwd = pathlib.Path(__file__).parent.resolve()
logging.config.fileConfig(
    os.path.join(cwd, "logging.conf"), disable_existing_loggers=False
)
logger = logging.getLogger("kpm")
logger.info("info")
logger.warning("warning")
logger.error("error")
logger.error("loglevel=" + logging.getLevelName(logger.getEffectiveLevel()))

app.logger = logger


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
