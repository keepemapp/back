from typing import Dict, List, Union

from pydantic import BaseModel


class FeedbackQuestion(BaseModel):
    order: int
    """Dictionary of questions per language"""
    question: Dict[str, str]
    type: str


class TextFeedbackQuestion(BaseModel):
    type: str = "text"


class BooleanFeedbackQuestion(BaseModel):
    type: str = "boolean"


class RatingFeedbackQuestion(BaseModel):
    type: str = "rating"
    values_min: int = 1
    name_min: Dict[str, str] = {
        "en": "Strongly Disagree",
    }
    values_max: int = 4
    name_max: Dict[str, str] = {
        "en": "Strongly Agree",
    }


class FeedbackForm(BaseModel):
    id: str
    title: Dict[str, str]
    created_ts: int
    questions: List[FeedbackQuestion]


class FeedbackQuestionResponse(BaseModel):
    form_id: str
    question_order: str
    response: Union[bool, int, str]
