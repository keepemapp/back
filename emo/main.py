from fastapi import FastAPI, Depends
import uvicorn

from emo.users.infrastructure.memory.repository import MemoryUserRepository
from emo.users.infrastructure.fastapi.v1 import users_router


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI(title="MyHeritage",)

app.include_router(users_router)


# Using FastAPI instance
@app.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)