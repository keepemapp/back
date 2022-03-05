import datetime
from typing import List

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params, paginate

from kpm.settings import settings as s
from kpm.shared.adapters.mongo import mongo_client
from kpm.shared.domain.time_utils import to_millis
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.users.entrypoints.fastapi.v1.schemas import feedback as sch

router = APIRouter(
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
    **s.API_FEEDBACK.dict(),
)


@router.get(
    "", responses={status.HTTP_200_OK: {"model": Page[sch.FeedbackForm]}}
)
async def list_feedback_forms(
    paginate_params: Params = Depends(),
    _: AccessToken = Depends(get_access_token),
):
    forms = [
        sch.FeedbackForm(
            id="1",
            title={
                "en": "Feedback",
                "ca": "Comentaris",
                "es": "Comentarios",
            },
            created_ts=to_millis(datetime.datetime(2022, 3, 5)),
            questions=[
                sch.BooleanFeedbackQuestion(
                    order=1,
                    question={
                        "en": """Twit length twit decription
                        Did you understood what the app is about?""",
                        "ca": """Descripció de l'aplicació
                        Has entès de què va?""",
                        "es": """Descripción
                        ¿Entendiste de qué va?""",
                    },
                ),
                sch.TextFeedbackQuestion(
                    order=2,
                    question={
                        "en": "Do you think it solves a need?",  # noqa:E501
                        "ca": "Creus que l'aplicació resol una necessitat?",  # noqa:E501
                        "es": "¿Crees que la aplicación soluciona una nacesidad?",  # noqa:E501
                    },
                ),
                sch.TextFeedbackQuestion(
                    order=3,
                    question={
                        "en": "Would you use it? How often?",
                        "ca": "La utilitzaries? Cada quant?",
                        "es": "¿La usarías? ¿Cada cuanto?",
                    },
                ),
                sch.TextFeedbackQuestion(
                    order=4,
                    question={
                        "en": "Would you pay for it? How much?",
                        "ca": "Pagaríes per usar-la? Quant?",
                        "es": "¿Pagarías por usarla? ¿Cuánto?",
                    },
                ),
                sch.TextFeedbackQuestion(
                    order=5,
                    question={
                        "en": "Do you want to tell us something else?",
                        "ca": "Vols fir-nos alguna cosa més?",
                        "es": "¿Quieres añadir algún comentario más?",
                    },
                ),
            ],
        ),
        sch.FeedbackForm(
            id="19e613d8-81b1-49f6-9e7e-296a2733bab4",
            title={
                "en": "Report bugs",
                "ca": "Comunica'ns errors",
                "es": "Reporta errores",
            },
            created_ts=to_millis(datetime.datetime(2022, 3, 5)),
            questions=[
                sch.TextFeedbackQuestion(
                    order=1,
                    question={
                        "en": "Please describe what happened and what were the actions you were doing in the app so we can check it out.",  # noqa:E501
                        "ca": "Siusplau descriu què ha passat i quines accions has fet perquè puguem revisar-ho més fàcilment.",  # noqa:E501
                        "es": "Por favor describa qué ha pasado y qué acciones has hecho para que podamos revisarlo más facilmente.",  # noqa:E501
                    },
                ),
            ]
        )
    ]

    return paginate(forms, paginate_params)


@router.post("", status_code=status.HTTP_200_OK)
async def add_feedback_responses(
    responses: List[sch.FeedbackQuestionResponse],
    token: AccessToken = Depends(get_access_token),
):
    if s.MONGODB_URL:
        with mongo_client() as client:
            col = client.users.feedback_response
            col.insert_many(
                [{"user": token.subject, **r.dict()} for r in responses]
            )
    else:
        pass
