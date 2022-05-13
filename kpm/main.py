import os
import random
import string
import time

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request

from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.settings import settings as s
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
    #servers=[
    #    {"url": "https://api.keepem.app", "description": "Production environment"},
    #    {"url": "http://localhost:8000", "description": "Staging environment"},
    #],
)

app.include_router(users_router)
app.include_router(assets_router)
app.include_router(common_endpoints.router)


app.logger = logger


@app.on_event("startup")
async def startup_event():
    logger.info("Application started", component="api")


@app.on_event("shutdown")
def shutdown_event():
    logger.warning("Application shutdown", component="api")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(
        {
            "rid": idem,
            "from_ip": request.client.host,  # use --forwarded-allow-ips *
            "method": request.method,
            "path": request.url.path,
        }, component="api"
    )
    start_time = time.time()
    # try:
    response = await call_next(request)
    status_code = response.status_code
    # except Exception as e:
        # process_time_ms = (time.time() - start_time) * 1000
        # logger.error(
        #     {
        #         "rid": idem,
        #         "path": request.url.path,
        #         "elapsed_ms": round(process_time_ms, 2),
        #         "status_code": 500,
        #         "message": str(e),
        #         "stack": str(traceback.format_exc())[-168:]
        #     }, component="api"
        # )
        #
        # return JSONResponse(status_code=500, content={
        #     "detail":
        #         f"Please give this code to support: '{idem}'. Error {str(e)}",
        # })

    process_time_ms = (time.time() - start_time) * 1000
    formatted_process_time = round(process_time_ms, 2)
    logger.info(
        {
            "rid": idem,
            "path": request.url.path,
            "method": request.method,
            "elapsed_ms": formatted_process_time,
            "status_code": status_code,
        }, component="api"
    )

    return response


if __name__ == "__main__":
    # Debug
    uvicorn.run(app, host="localhost", port=8000, access_log=False)
