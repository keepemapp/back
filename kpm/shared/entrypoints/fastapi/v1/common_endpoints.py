import os

from fastapi import APIRouter, Depends

from kpm.assets.adapters.filestorage import AssetFileLocalRepository
from kpm.assets.entrypoints.fastapi.dependencies import asset_file_repository
from kpm.settings import settings as s
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    prefix=s.API_V1.prefix, responses={404: {"description": "Not found"}}
)


@router.get(s.API_HEALTH.path(), status_code=200)
async def get_health(
        _: MessageBus = Depends(message_bus),
        file_repo: AssetFileLocalRepository = Depends(asset_file_repository)
):
    return "OK"


@router.get(s.API_VERSION.path(), status_code=200)
async def get_version():
    version = "N/A"
    branch = "N/A"
    if os.name != "nt":
        import git

        repo = git.Repo(search_parent_directories=True)
        version = repo.git.rev_parse(repo.head, short=True)
        branch = repo.active_branch

    return {"branch": branch, "version": version}
