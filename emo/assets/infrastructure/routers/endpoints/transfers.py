from fastapi import APIRouter
from typing import List, Any
from fastapi import FastAPI, File, UploadFile, Form, Depends
import uuid

import datetime

from api import schemas

router = APIRouter(
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Transfer])
async def get_transfers():
    return [schemas.Transfer(id=str(uuid.uuid4()),
                             title="Transfer title",
                             scheduled_date=datetime.datetime.utcnow(),
                             file_ids=["file1", "file2"],
                             transferer_id="userWhoTrasnfers",
                             receiver_ids=["target_user"],
                             )
            ]


@router.get("/{transfer_id}", response_model=schemas.Transfer)
async def get_transfer(transfer_id: str):
    return schemas.Transfer(id=transfer_id,
                            title="Transfer title",
                            scheduled_date=datetime.datetime.utcnow(),
                            file_ids=["file1", "file2"],
                            transferer_id="userWhoTrasnfers",
                            receiver_ids=["target_user"],
                            )


@router.post("/", response_model=schemas.Transfer)
async def create_transfer(*, transfer: schemas.TransferCreate) -> Any:

    pass