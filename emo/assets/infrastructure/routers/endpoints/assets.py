import uuid
from typing import List

from api import schemas
from fastapi import APIRouter, File, Form, UploadFile

router = APIRouter(
    responses={404: {"description": "Not found"}},
)


def create_random_asset():
    id = str(uuid.uuid4())
    return schemas.Asset(
        id=id,
        title="MyAsset",
        owner_id=str(uuid.uuid4()),
        type="image",
        file_name="myfile.png",
    )


@router.get("/", response_model=List[schemas.Asset])
async def get_assets():
    return [create_random_asset() for _ in range(4)]


def create_user_dir(user_id: str):
    import os

    user_dir = "assets/" + user_id
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)


def write_asset(user_id: str, asset_id: uuid.UUID, file: UploadFile):
    file_location = f"assets/{user_id}/{asset_id}.enc"
    create_user_dir(user_id)
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())


@router.post("/", response_model=schemas.Asset)
async def create_asset(file: UploadFile = File(...), assetname: str = Form(...)):
    id = str(uuid.uuid4())
    write_asset("userId", id, file)
    # TODO save meta information
    return schemas.Asset(
        id=id,
        title=assetname,
        owner_id="userId",
        type=file.content_type,
        file_name=file.filename,
    )


@router.get("/{asset_id}", response_model=schemas.Asset)
async def get_asset(asset_id: str):
    return schemas.Asset(
        id=asset_id,
        title="MyAsset",
        owner_id=str(uuid.uuid4()),
        type="image",
        file_name="myfile.png",
    )
