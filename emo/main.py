import uvicorn
from fastapi import FastAPI

from emo.users.infra.fastapi.v1 import users_router

app = FastAPI(
    title="MyHeritage",
)

app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
