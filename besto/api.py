from fakit import api
from typing import Dict
from pydantic import BaseModel


class Result(BaseModel):
    message: str


class Input(BaseModel):
    name: str


@api.post("/testQQ")
def testQQ(input: Input) -> Result:
    return Result(message=f"Hello {input.name}")
