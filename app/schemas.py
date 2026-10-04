import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TransactionIn(BaseModel):
    kind: Literal["income", "expense"]
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)
    date: dt.date


class TransactionOut(TransactionIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class Summary(BaseModel):
    income: float
    expense: float
    balance: float
    by_category: dict[str, float]
    by_month: dict[str, dict[str, float]]
