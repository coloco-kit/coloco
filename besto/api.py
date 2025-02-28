from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def thebestest():
    return {"Hello": "World"}


@router.get("/testerino", name="besto.testerinozz")
def testerinozz(name: str):
    return {"Hello": name}


@router.get("/testerbb/{name}")
def testerbb(name: str):
    return {"Hello": name}


dong = testerbb("HEYY")
