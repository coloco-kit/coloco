from fakit import api
from typing import Dict


@api
def thebestest() -> Dict[str, str]:
    return {"Hello": "World"}


@api.get("/testerino", summary="This is a testerinozz")
def testerinozz(name: str):
    return {"Hello": name}


@api.get("/testerbb/{name}")
def testerbb(name: str):
    return {"Hello": name}


dong = testerbb("HEYY")
