import os

from fastapi import APIRouter

from kpm.settings import settings as s

router = APIRouter(
    prefix=s.API_V1.prefix, responses={404: {"description": "Not found"}}
)


@router.get(s.API_HEALTH.path(), status_code=200)
async def get_health():
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
