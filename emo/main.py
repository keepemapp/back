from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from enum import Enum
from fastapi_login import LoginManager
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

from emo.infrastructure.routers import api_router

app = FastAPI(
    title="MyHeritage",
)

app.include_router(api_router)

class AssetType(str, Enum):
    image = "image"
    video = "video"
    audio = "audio"
    document = "document"
    other = "other"

# TODO move me to env variable
SECRET = "8ab5b651555ef56bbb27e84868034dd7cb9d6533bf2bb16b"
manager = LoginManager(SECRET, '/login',
)
manager.cookie_name = 'emo-auth-cookie'
DB = {
    'users': {
        'user1': {
            'id': '30012f50-f754-43ef-b501-e0a2ab885aa1',
            'name': 'user1',
            'password': 'password'
        },
        'user2': {
            'id': 'ff661881-97fa-46bc-9a28-0bfb46f02c78',
            'name': 'user2',
            'password': 'password'
        }
    }
}

@manager.user_loader
def query_user(user_id: str):
    """
    Get a user from the db
    :param user_id: username of the user
    :return: None or the user object
    """
    return DB['users'].get(user_id)

@app.get("/login")
async def main():
    content = """
<body>
<form action="/login" enctype="multipart/form-data" method="post">
<label for="username">Asset name:</label><br>
<input type="text" id="username" name="username"><br>
<label for="password">Password:</label><br>
<input type="text" id="password" name="password"><br>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)

@app.post('/login')
def login(data: OAuth2PasswordRequestForm = Depends()):
    email = data.username
    password = data.password

    user = query_user(email)
    if not user:
        # you can return any response or error of your choice
        raise InvalidCredentialsException
    elif password != user['password']:
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data={'sub': email}
    )
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/upload")
async def main():
    content = """
<body>
<form action="/assets/" enctype="multipart/form-data" method="post">
<label for="assetname">Asset name:</label><br>
<input type="text" id="assetname" name="assetname"><br>
<input name="file" id="file" type="file">
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)




@app.get('/proteced')
def protected_route(user=Depends(manager)):
    return {'user': user}