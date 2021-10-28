import logging
import random
import string
import time
import uvicorn
from fastapi import FastAPI, Request

from emo.assets.infra.fastapi.v1 import assets_router
from emo.users.infra.fastapi.v1 import users_router

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MyHeritage",
)

app.include_router(users_router)
app.include_router(assets_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(
        '{"rid":"%s", "method":"%s", "path": "%s"}',
        idem, request.method, request.url.path
    )
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(
        '{"rid":"%s", "completed_in":"%sms", "status_code":"%s"}',
        idem, formatted_process_time, response.status_code
    )

    return response


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        logger=logger
    )
